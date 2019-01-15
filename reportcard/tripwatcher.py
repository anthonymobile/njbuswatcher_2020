import argparse
import itertools
import numpy as np
import scipy
import time
from lib import BusAPI, Localizer
from lib import DataBases as db

# args = source, route
parser = argparse.ArgumentParser()
parser.add_argument('-s', '--source', dest='source', default='nj', help='source name')
parser.add_argument('-r', '--route', dest='route', required=True, help='route number')
args = parser.parse_args()

while True:
    delay = 60
    print (('\nPlease wait {a} seconds for next run...').format(a=delay))
    time.sleep(delay)

    ##############################################
    # FETCH AND LOCALIZE CURRENT POSITIONS
    ##############################################
    buses = BusAPI.parse_xml_getBusesForRoute(BusAPI.get_xml_data(args.source,'buses_for_route',route=args.route))
    bus_positions = Localizer.get_nearest_stop(buses,args.route)
    session = db.BusPosition.get_session()
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
            result = session.query(db.Trip).filter(db.Trip.trip_id == bus.trip_id).first()
            if result is None:
                trip = db.Trip(args.source, args.route, bus.id, bus.run)
                print (('Created a new trip record for {a}').format(a=bus.trip_id))
                session = db.Trip.get_session()
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
        scheduled_stops = session.query(db.Trip,db.ScheduledStop)\
            .join(db.ScheduledStop) \
            .filter(db.Trip.trip_id == trip) \
            .all()

        # select  all the BusPositions on ScheduledStops where there is no arrival flag yet
        arrival_candidates = session.query(db.BusPosition) \
            .join(db.ScheduledStop) \
            .filter(db.BusPosition.trip_id == trip) \
            .filter(db.ScheduledStop.arrival_timestamp == None) \
            .order_by(db.BusPosition.timestamp.asc()) \
            .all()

        # for bus in arrival_candidates:
        #     print (('\t(BusPosition) stop_id {a}  distance_to_stop {b:.0f} timestamp {c} ').format(c=bus.timestamp, a=bus.stop_id, b=bus.distance_to_stop))

        # groupby stop_id
        position_groups = [list(g) for key, g in itertools.groupby(arrival_candidates, lambda x: x.stop_id)]


        # now loop over the position_groups (except for last one which is current but location) and see if we can assign an arrival time

        case_frequencies = {'caseA': 0, 'caseB': 0, 'caseC': 0, 'caseD': 0, }
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
                    case_frequencies['caseA'] += 1
                    print('caseA {a}'.format(a=arrival_time))

                # CASE B approaches, then vanishes
                # determined by [d is decreasing, slope is always negative]
                # (0, 400)
                # (1, 300) <-----
                elif slope_avg < 0:
                    arrival_time = position_list[-1].timestamp
                    position_list[-1].arrival_flag = True
                    case_frequencies['caseB'] += 1
                    print('caseB {a}'.format(a=arrival_time))

                # CASE C appears, then departs
                # determined by [d is increasing, slope is always positive]
                # (0, 50)  <-----
                # (1, 100)
                elif (slope_avg > 0):
                    arrival_time = position_list[0].timestamp
                    position_list[0].arrival_flag = True
                    case_frequencies['caseC'] += 1
                    print('caseC {a}'.format(a=arrival_time))


            ##############################################
            #   THREE OR MORE POSITIONS
            #
            #   simple method = take the earliest minimum value
            #
            #   complex method =
            #   polyfit a curve
            #   find the min within the bounds of
            #   range of observed distance_to_stop
            #   round it to nearest integer
            #   take that position in the position_list[rounded]
            ##############################################



            elif len(position_list) > 2:

                ##############################################
                #   SIMPLE
                ##############################################

                # create and display approach array
                print (('\n\tapproaching {b}').format(a=trip, b=position_list[0].stop_id))
                points=[]
                for y in range(len(position_list)):
                    points.append((y,position_list[y].distance_to_stop))
                approach_array = np.array(points)
                for point in approach_array:
                    print (('\t\t {a:.0f} distance_to_stop {b}').format(a=point[0], b=point[1]))

                # find the lowest value(s) and take the first one
                mins_indices = np.argmin(approach_array, axis=0)
                arrival_time = position_list[mins_indices[0]].timestamp

                position_list[0].arrival_flag = True
                case_frequencies['caseD'] += 1
                print('caseD {a}'.format(a=arrival_time))

                ##############################################
                #   COMPLEX
                ##############################################
                #
                # # create and display approach array
                # print (('\n\tapproaching {b}').format(a=trip, b=position_list[0].stop_id))
                # points=[]
                # for y in range(len(position_list)):
                #     points.append((y,position_list[y].distance_to_stop))
                # approach_array = np.array(points)
                # for point in approach_array:
                #     print (('\t\t {a:.0f} distance_to_stop {b}').format(a=point[0], b=point[1]))
                #
                # # polyfit a curve
                # try:
                #     z_quad = np.polyfit(approach_array[:, 0], approach_array[:, 1], 2)
                #
                #     if z_quad[0] > 0:
                #         # https://stackoverflow.com/questions/29634217/get-minimum-points-of-numpy-poly1d-curve
                #         c = np.poly1d(z_quad)
                #         crit = c.deriv().r
                #         r_crit = crit[crit.imag == 0].real
                #         test = c.deriv(2)(r_crit)
                #         x_min = r_crit[test > 0]
                #         # y_min = c(x_min)
                #         arrival_position = int(round(x_min))-1 # round to nearest position in the approach_array

                #         arrival_time = position_list[arrival_position].timestamp
                #         position_list[arrival_position].arrival_flag = True
                #         print ('caseD {a}'.format(a=arrival_time))
                #         case_frequencies['caseD'] += 1
                #
                #     else:
                #         # negative slope = case B
                #         if z_quad[1] < 0:
                #             arrival_time = position_list[-1].timestamp
                #             position_list[-1].arrival_flag = True
                #             case_frequencies['caseB'] += 1
                #             print('caseB {a}'.format(a=arrival_time))
                #
                #         # positive slope = case C
                #         elif z_quad[1] > 0:
                #             arrival_time = position_list[0].timestamp
                #             position_list[0].arrival_flag = True
                #             case_frequencies['caseC'] += 1
                #             print('caseC {a}'.format(a=arrival_time))
                #
                # except:
                #     pass

        print (case_frequencies)

        session.commit() # sends any updates made above (like setting the arrival flag

        # 4
        # update the database
        # get a session
        #
        # add position_update to the session as table update
        # log the arrival_timestamp for corresponding ScheduledStop
        # session.commit()
