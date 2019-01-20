import argparse
import itertools
import numpy as np
import scipy
import time
from lib import BusAPI, Localizer
#from lib import DataBases as db
from lib.DataBases import Trip,BusPosition,ScheduledStop

# args = source, route
parser = argparse.ArgumentParser()
parser.add_argument('-s', '--source', dest='source', default='nj', help='source name')
parser.add_argument('-r', '--route', dest='route', required=True, help='route number')
args = parser.parse_args()

while True:
    delay = 30
    print (('\nPlease wait {a} seconds for next run...').format(a=delay))
    time.sleep(delay)

    ##############################################
    # FETCH AND LOCALIZE CURRENT POSITIONS
    ##############################################
    buses = BusAPI.parse_xml_getBusesForRoute(BusAPI.get_xml_data(args.source,'buses_for_route',route=args.route))
    bus_positions = Localizer.get_nearest_stop(buses,args.route)
    session = BusPosition.get_session()
    for group in bus_positions:
        for bus in group:
            session.add(bus)
    session.commit()
    print('<----observed positions and new trips---->')
    print ('trip_id\t\t\t\t\tv\t\trun\tstop_id\tdistance_to_stop (feet)')
    for direction in bus_positions:
       for b in direction:
           print (('t{a}\t\t{b}\t{c}\t{d}\t{e:.0f}').format(a=b.trip_id,b=b.id,c=b.run,d=b.stop_id,e=b.distance_to_stop))

    ##############################################
    #   CREATE TRIP RECORDS FOR ANY NEW TRIPS SEEN
    ##############################################
    triplist=[]
    for busgroup in bus_positions:
        for bus in busgroup:
            triplist.append(bus.trip_id)
            result = session.query(Trip).filter(Trip.trip_id == bus.trip_id).first()
            if result is None:
                trip = Trip(args.source, args.route, bus.id, bus.run)
                print (('Created a new trip record for {a}').format(a=bus.trip_id))
                session = Trip.get_session()
                session.add(trip)
                session.commit()

            else:
                pass

    ##############################################
    #   ASSIGN ARRIVALS
    ##############################################

    for trip in triplist:
        print(('analyzing arrival candidates on trip {a}...').format(a=trip))

        # load the trip card for reference
        scheduled_stops = session.query(Trip,ScheduledStop)\
            .join(ScheduledStop) \
            .filter(Trip.trip_id == trip) \
            .all()

        # select  all the BusPositions on ScheduledStops where there is no arrival flag yet
        arrival_candidates = session.query(BusPosition) \
            .join(ScheduledStop) \
            .filter(BusPosition.trip_id == trip) \
            .filter(ScheduledStop.arrival_timestamp == None) \
            .order_by(BusPosition.timestamp.asc()) \
            .all()

        # for bus in arrival_candidates:
        #     print (('\t(BusPosition) stop_id {a}  distance_to_stop {b:.0f} timestamp {c} ').format(c=bus.timestamp, a=bus.stop_id, b=bus.distance_to_stop))

        # groupby stop_id
        position_groups = [list(g) for key, g in itertools.groupby(arrival_candidates, lambda x: x.stop_id)]


        # now loop over the position_groups (except for last one which is current but location) and see if we can assign an arrival time

        for x in range (len(position_groups)-1):

            position_list = position_groups[x]

            ##############################################
            #   ONE POSITION
            #   if we only have one observation and since
            #   this isn't the current stop, then we've
            #   already passed it and can just assign it
            #   as the arrival
            ##############################################

            if len(position_list) == 1:
                print(('\n\tapproaching {b}').format(a=trip, b=position_list[0].stop_id))
                arrival_time = position_list[0].timestamp
                position_list[0].arrival_flag = True
                #print('case1A {a}'.format(a=arrival_time))
                print('case1A position0')

                # select the ScheduleStop where trip_id and stop_id are the same as for this BusPosition
                # & update the ScheduledStop arrival_timestamp to the arrival_time
                stop_to_update = session.query(ScheduledStop, BusPosition) \
                    .join(BusPosition) \
                    .filter(ScheduledStop.stop_id == position_list[0].stop_id) \
                    .all()
                stop_to_update[0][0].arrival_timestamp = arrival_time

                # todo check all ScheduledStops with positions for arrival_flag and interpolate any missing ones -- with scipy?

            ##############################################
            #   TWO POSITIONS
            #   calculate the slope between the two points
            #   and assign to CASE A,B, or C
            #   arrival is either the 1st observed position
            #   or the 2nd
            ##############################################

            elif len(position_list) == 2:

                # create and display approach array
                print (('\n\tapproaching {b}').format(a=trip, b=position_list[0].stop_id))
                points=[]
                for y in range(len(position_list)):
                    points.append((y,position_list[y].distance_to_stop))
                approach_array = np.array(points)
                for point in approach_array:
                    print (('\t\t {a:.0f} distance_to_stop {b}').format(a=point[0], b=point[1]))

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
                    # todo set ScheduleStop.arrival_position = position_list[0].pkey
                    #print('case2A {a}'.format(a=arrival_time))
                    print('case2A position0')

                # CASE B approaches, then vanishes
                # determined by [d is decreasing, slope is always negative]
                # (0, 400)
                # (1, 300) <-----
                elif slope_avg < 0:
                    arrival_time = position_list[-1].timestamp
                    position_list[-1].arrival_flag = True
                    # todo set ScheduleStop.arrival_position = position_list[0].pkey
                    #print('case2B {a}'.format(a=arrival_time))
                    print('case2B position(last)')

                # CASE C appears, then departs
                # determined by [d is increasing, slope is always positive]
                # (0, 50)  <-----
                # (1, 100)
                elif (slope_avg > 0):
                    arrival_time = position_list[0].timestamp
                    position_list[0].arrival_flag = True
                    # todo set ScheduleStop.arrival_position = position_list[0].pkey
                    #print('case2C {a}'.format(a=arrival_time))
                    print('case2C position0')


            ##############################################
            #   THREE OR MORE POSITIONS
            ##############################################

            elif len(position_list) > 2:

                # create and display approach array
                print(('\n\tapproaching {b}').format(a=trip, b=position_list[0].stop_id))
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

                    # # CASE D if the min position is more than 0 and less than last position, its a D
                    # if np.argmin(approach_array, axis=1) >0 and np.argmin(approach_array, axis=1) < len(position_list):
                    #
                    #     z_quad = np.polyfit(approach_array[:, 0], approach_array[:, 1], 2)
                    #     # find the min
                    #     # https://stackoverflow.com/questions/29634217/get-minimum-points-of-numpy-poly1d-curve
                    #     c = np.poly1d(z_quad)
                    #     crit = c.deriv().r
                    #     r_crit = crit[crit.imag == 0].real
                    #     test = c.deriv(2)(r_crit)
                    #     x_min = r_crit[test > 0]
                    #     arrival_position = int(round(x_min))-1 # round to nearest position in the approach_array
                    #     arrival_time = position_list[arrival_position].timestamp
                    #     position_list[arrival_position].arrival_flag = True
                    #     print ('caseD {a}'.format(a=arrival_time))
                    #     case_frequencies['caseD'] += 1

                    # CASE A
                    if slope_avg == 0:
                        arrival_time = position_list[0].timestamp
                        position_list[0].arrival_flag = True
                        # todo set ScheduleStop.arrival_position = position_list[0].pkey
                        #print('case3A {a}'.format(a=arrival_time))
                        print('case3A position0')

                    # CASE B
                    elif slope_avg < 0:
                        arrival_time = position_list[-1].timestamp
                        position_list[-1].arrival_flag = True
                        # todo set ScheduleStop.arrival_position = position_list[0].pkey
                        #print('case3B {a}'.format(a=arrival_time))
                        print('case3B position(last)')


                    # CASE C
                    elif slope_avg > 0:
                        arrival_time = position_list[0].timestamp
                        position_list[0].arrival_flag = True
                        # todo set ScheduleStop.arrival_position = position_list[0].pkey
                        #print('case3C {a}'.format(a=arrival_time))
                        print('case3C position0')

                except:
                    pass

        session.commit() # update the arrival_flags and points from ScheduledStop-->BusPosition
