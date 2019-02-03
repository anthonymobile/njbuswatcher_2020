
# # database setting
#conn_str = 'sqlite:///jc_buswatcher.db'

import argparse
import os, sys
import werkzeug
import itertools
import numpy as np
import matplotlib.pyplot as plt
import scipy
import time
from lib import BusAPI, Localizer
from lib.DataBases import DBConfig, SQLAlchemyDBConnection, Trip, BusPosition, ScheduledStop

def plot_approach(trip_id, approach_array,case_identifier):
    x = [row[0] for row in approach_array]
    y = [row[1] for row in approach_array]
    # x = approach_array[:,0]
    # y = approach_array[:,1]
    x_max = np.max(x)
    y_max = np.max(y)
    plt.scatter(x, y)
    label = ('{a} {b}').format(a=trip_id, b=case_identifier)
    plt.xlabel(label)
    plt.axis([0, 1.1 * x_max, 0, 1.1 * y_max])
    plt.show()
    print ('plot failed')
    return

if __name__ == "__main__":

    # args
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', dest='source', default='nj', help='source name')
    parser.add_argument('-r', '--route', dest='route', required=True, help='route number')
    args = parser.parse_args()

    ran = False

    while True:

        if ran == True:
            delay = 30
        else:
            delay = 0

        print (('\nPlease wait {a} seconds for next run...').format(a=delay))
        time.sleep(delay)

        ##############################################
        # 1 -- FETCH AND LOCALIZE CURRENT POSITIONS
        ##############################################

        with SQLAlchemyDBConnection(DBConfig.conn_str) as db:

            # get buses from NJT API
            while True:
                try:
                    buses = BusAPI.parse_xml_getBusesForRoute(
                        BusAPI.get_xml_data(args.source, 'buses_for_route', route=args.route))
                except werkzeug.exceptions.NotFound as e:
                    sys.stdout.write('.')
                    # time.sleep(2)
                    continue
                break


            bus_positions = Localizer.get_nearest_stop(buses,args.route)
            for group in bus_positions:
                for bus in group:
                    db.session.add(bus)
            db.session.commit()
            print('\n<----observed positions---->')
            print ('trip_id\t\t\t\tv\trun\tstop_id\tdistance_to_stop (feet)')
            for direction in bus_positions:
               for b in direction:
                   print (('t{a}\t\t{b}\t{c}\t{d}\t{e:.0f}').format(a=b.trip_id,b=b.id,c=b.run,d=b.stop_id,e=b.distance_to_stop))

            #   create trip records for any new trips seen
            triplist = []
            for busgroup in bus_positions:
                for bus in busgroup:
                    triplist.append(bus.trip_id)
                    result = db.session.query(Trip).filter(Trip.trip_id == bus.trip_id).first()
                    if result is None:
                        print(('Created a new trip record for {a}').format(a=bus.trip_id))
                        trip_id = Trip(DBConfig.conn_str, args.source, args.route, bus.id, bus.run, bus.pid)
                        db.session.add(trip_id)

                    else:
                        pass
                    db.session.commit()


        ##############################################
        #   2 -- ASSIGN ARRIVALS
        ##############################################

        with SQLAlchemyDBConnection(DBConfig.conn_str) as db:

            print('\n<----approach analysis---->')
            for trip_id in triplist:
                print(('trip {a}...').format(a=trip_id))

                # load the trip card for reference
                scheduled_stops = db.session.query(Trip,ScheduledStop)\
                    .join(ScheduledStop) \
                    .filter(Trip.trip_id == trip_id) \
                    .all()

                # select all the BusPositions on ScheduledStops where there is no arrival flag yet
                arrival_candidates = db.session.query(BusPosition) \
                    .join(ScheduledStop) \
                    .filter(BusPosition.trip_id == trip_id) \
                    .filter(ScheduledStop.arrival_timestamp == None) \
                    .order_by(BusPosition.timestamp.asc()) \
                    .all()

                # split them into groups by stop
                position_groups = [list(g) for key, g in itertools.groupby(arrival_candidates, lambda x: x.stop_id)]

                # iterate over all but last one (which is stop bus is currently observed at)
                for x in range (len(position_groups)-1):

                    # slice the positions for the xth stop
                    position_list = position_groups[x]

                    # GRAB THE STOP RECORD FROM DB FOR UPDATING ARRIVAL INFO
                    stop_to_update = db.session.query(ScheduledStop, BusPosition) \
                        .join(BusPosition) \
                        .filter(ScheduledStop.trip_id == position_list[0].trip_id) \
                        .filter(ScheduledStop.stop_id == position_list[0].stop_id) \
                        .all()

                    ##############################################
                    #   ONE POSITION
                    #   if we only have one observation and since
                    #   this isn't the current stop, then we've
                    #   already passed it and can just assign it
                    #   as the arrival
                    ##############################################

                    if len(position_list) == 1:
                        print(('\tapproaching {a}').format(a=position_list[0].stop_id))
                        arrival_time = position_list[0].timestamp
                        position_list[0].arrival_flag = True
                        print(('\t\t 0.0,{a:.0f} distance_to_stop {a:.0f}').format(a=position_list[0].distance_to_stop))
                        case_identifier='1a'
                        approach_array=np.array([0,position_list[0].distance_to_stop])
                        # plot_approach(trip_id,approach_array,case_identifier)

                    ##############################################
                    #   TWO POSITIONS
                    #   calculate the slope between the two points
                    #   and assign to CASE A,B, or C
                    #   arrival is either the 1st observed position
                    #   or the 2nd
                    ##############################################

                    elif len(position_list) == 2:

                        # create and display approach array
                        print (('\tapproaching {b}').format(a=trip_id, b=position_list[0].stop_id))
                        points=[]
                        for y in range(len(position_list)):
                            points.append((y,position_list[y].distance_to_stop))
                        approach_array = np.array(points)
                        for point in approach_array:
                            print (('\t\t\t{a:.0f} distance_to_stop {b}').format(a=point[0], b=point[1]))

                        # calculate classification metrics
                        slope = np.diff(approach_array, axis=0)[:, 1]
                        acceleration = np.diff(slope, axis=0)
                        slope_avg = np.mean(slope, axis=0)

                        # CASE A sitting at the stop, then gone without a trace
                        # determined by [d is <100, doesn't change e.g. slope = 0 ]
                        # (0, 50)  <-----
                        # (1, 50)
                        if slope_avg == 0:
                            arrival_time = position_list[0].timestamp
                            position_list[0].arrival_flag = True
                            case_identifier = '2a'
                            # plot_approach(trip_id, np.array([0, position_list[0].distance_to_stop]), case_identifier)

                        # CASE B approaches, then vanishes
                        # determined by [d is decreasing, slope is always negative]
                        # (0, 400)
                        # (1, 300) <-----
                        elif slope_avg < 0:
                            arrival_time = position_list[-1].timestamp
                            position_list[-1].arrival_flag = True
                            case_identifier = '2b'
                            # plot_approach(trip_id, np.array([0, position_list[-1].distance_to_stop]), case_identifier)

                        # CASE C appears, then departs
                        # determined by [d is increasing, slope is always positive]
                        # (0, 50)  <-----
                        # (1, 100)
                        elif slope_avg > 0:
                            arrival_time = position_list[0].timestamp
                            position_list[0].arrival_flag = True
                            case_identifier = '2c'
                            # plot_approach(trip_id, np.array([0, position_list[0].distance_to_stop]), case_identifier)

                    ##############################################
                    #   THREE OR MORE POSITIONS
                    ##############################################

                    elif len(position_list) > 2:

                        # create and display approach array
                        print(('\tapproaching {b}').format(a=trip_id, b=position_list[0].stop_id))
                        points = []
                        for y in range(len(position_list)):
                            points.append((y, position_list[y].distance_to_stop))
                        approach_array = np.array(points)
                        for point in approach_array:
                            print(('\t\t {a:.0f} distance_to_stop {b}').format(a=point[0], b=point[1]))

                        # calculate classification metrics
                        slope = np.diff(approach_array, axis=0)[:, 1]
                        acceleration = np.diff(slope, axis=0)
                        slope_avg = np.mean(slope, axis=0)

                        try:
                            # CASE A
                            if slope_avg == 0:
                                arrival_time = position_list[0].timestamp
                                position_list[0].arrival_flag = True
                                case_identifier = '3a'
                                # plot_approach(trip_id, np.array([0, position_list[0].distance_to_stop]), case_identifier)

                            # CASE B
                            elif slope_avg < 0:
                                arrival_time = position_list[-1].timestamp
                                position_list[-1].arrival_flag = True
                                case_identifier = '3b'
                                # plot_approach(trip_id, np.array([0, position_list[-1].distance_to_stop]), case_identifier)

                            # CASE C
                            elif slope_avg > 0:
                                arrival_time = position_list[0].timestamp
                                position_list[0].arrival_flag = True
                                case_identifier = '3c'
                                # plot_approach(trip_id, np.array([0, position_list[0].distance_to_stop]), case_identifier)

                        except:
                            pass

                    # catch errors for unassigned 3+-position approaches
                    try:
                        stop_to_update[0][0].arrival_timestamp = arrival_time
                    except:
                        pass

            db.session.commit()

        ran = True
