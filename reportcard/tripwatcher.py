import argparse, itertools
import numpy as np

# args = source, route
parser = argparse.ArgumentParser()
parser.add_argument('-s', '--source', dest='source', default='nj', help='source name')
parser.add_argument('-r', '--route', dest='route', required=True, help='route number')

args = parser.parse_args()

from lib import BusAPI, Localizer
from lib import DataBases as db

import scipy

import time
while True:
    delay = 60
    print (('\nPlease wait {a} seconds for next run...').format(a=delay))
    time.sleep(delay)


    ##############################################
    #
    #   FETCH AND LOCALIZE CURRENT POSITIONS
    #
    ##############################################


    # 1 fetch all buses on route currently
    # buses = a list of Bus objects
    buses = BusAPI.parse_xml_getBusesForRoute(BusAPI.get_xml_data(args.source,'buses_for_route',route=args.route))

    # 2 localize them to nearest stop and log to db
    # bus_positions = list of BusPosition objects
    bus_positions = Localizer.get_nearest_stop(buses,args.route)
    session = db.BusPosition.get_session()
    for group in bus_positions:
        for bus in group:
            session.add(bus)
    session.commit()

    # 3 generate some diagnostic output of what we just tracked
    print('<----observed positions and new trips---->')
    print ('trip_id\t\t\t\t\tv\t\trun\tstop_id\tdistance_to_stop (feet)')
    for direction in bus_positions:
       for b in direction:
           print (('t{a}\t\t{b}\t{c}\t{d}\t{e:.0f}').format(a=b.trip_id,b=b.id,c=b.run,d=b.stop_id,e=b.distance_to_stop))

    ##############################################
    #
    #   CREATE TRIP RECORDS FOR ANY NEW TRIPS SEEN
    #
    ##############################################

    triplist=[]

    # loop over the buses
    for busgroup in bus_positions:
        for bus in busgroup:

            triplist.append(bus.trip_id)
            result = session.query(db.Trip).filter(db.Trip.trip_id == bus.trip_id).first()

            # if there is no Trip record yet, create one
            if result is None:
                trip = db.Trip(args.source, args.route, bus.id, bus.run)
                print (('Created a new trip record for {a}').format(a=bus.trip_id))

                session = db.Trip.get_session()
                session.add(trip)
                session.commit()

            # otherwise nothing
            else:
                pass



    ##############################################
    #
    #   ASSIGN ARRIVALS
    #
    ##############################################

    position_update=[]

    # for each trip
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

            # EASIEST / CLEANUP
            # if we only have one observation and since this isn't the current stop,
            # then we've already passed it and can just assign it as the arrival

            if len(position_list) == 1:
                assigned_BusPosition = position_list[0]
                position_list[0].arrival_flag = True

                position_update.append(position_list[0])

                # 3
                # check all ScheduledStops with positions for arrival_flag and interpolate any missing ones
                # can we do it with scipy?

            # OTHERWISE
            else:

                # 1 create approach array
                # (n, distance) for these BusPositions

                print (('\n\tapproaching {b}').format(a=trip, b=position_list[0].stop_id))

                points=[]
                for y in range(len(position_list)):
                    points.append((y,position_list[y].distance_to_stop))
                approach_array = np.array(points)

                for point in approach_array:
                    print (('\t\t {a:.0f} distance_to_stop {b}').format(a=point[0], b=point[1]))




                ################################################33
                #
                #
                ######## DEBUGGING

                UNASSIGNED
                TRIPS

                analyzing
                arrival
                candidates
                on
                trip
                5739_15_20190114...

                # these 3 suggests --- test for # of positions is not good for filtering
                # polyfit these also....?
                # or just do a simple slope?
                # is there one approach for anything over 2 positions that can filter B,C from D?
                #             approaching
                #             20610
                #             0
                #             distance_to_stop
                #             210.16058526919383
                #             1
                #             distance_to_stop
                #             210.16058526919383
                #             2
                #             distance_to_stop
                #             274.4702380028972
                #
                #         approaching
                #         20496
                #         0
                #         distance_to_stop
                #         1.5360106211100863
                #         1
                #         distance_to_stop
                #         1.5360106211100863
                #         2
                #         distance_to_stop
                #         1.5360106211100863
                #         3
                #         distance_to_stop
                #         1.5360106211100863
                #         4
                #         distance_to_stop
                #         1.5360106211100863
                #         5
                #         distance_to_stop
                #         196.9567041019691
                #
                #     approaching
                #     31731
                #     0
                #     distance_to_stop
                #     260.09398414587315
                #     1
                #     distance_to_stop
                #     318.33337343873944
                #     2
                #     distance_to_stop
                #     318.33337343873944
                #     3
                #     distance_to_stop
                #     616.3932991517729
                #
                # # this one suggests +/- 10 percent error on the distance to stop?
                # approaching
                # 21066
                # 0
                # distance_to_stop
                # 588.4626107067455
                # 1
                # distance_to_stop
                # 595.9485389675923
                # 2
                # distance_to_stop
                # 62.383752097023596


                # if its a case D
                # CASE D approach, stop, depart
                # determined by [d is decreasing, slope is negative, then inverts and d is decreasing, slope is increasing, assign to point of lowest d]
                # (0, 200)
                # (1, 100) ***
                # (2, 200)
                # (3, 300)
                # ASSIGNMENT
                # arrival_time = (1)

                if len(position_list) > 2:
                    # polyfit the line
                    try:

                        z_quad = np.polyfit(approach_array[:, 0], approach_array[:, 1], 2)

                        # if the coefficient on x2 is positive, we are concave up and this is definitely a CASE D:
                        if z_quad[0] > 0:

                            # https://stackoverflow.com/questions/29634217/get-minimum-points-of-numpy-poly1d-curve
                            c = np.poly1d(z_quad)
                            crit = c.deriv().r
                            r_crit = crit[crit.imag == 0].real
                            test = c.deriv(2)(r_crit)

                            # compute local minima
                            # excluding range boundaries
                            x_min = r_crit[test > 0]
                            y_min = c(x_min)

                            arrival_position = int(round(x_min))-1 # round to nearest position in the approach_array
                            # todo for position in approach_array: check that this is indeed the minimum

                            arrival_time = position_list[arrival_position].timestamp
                            print ('caseD {a}'.format(a=arrival_time))
                            case_frequencies['caseD'] += 1

                    except:
                        pass

                # just do the working case A,B,C filter
                else:

                    # old fit to line
                    # z_line = np.polyfit(approach_array[:, 0], approach_array[:, 1], 1)

                    # calculate classification metrics

                    slope = np.diff(approach_array, axis=0)[:, 1]
                    acceleration = np.diff(slope, axis=0)
                    slope_avg=np.mean(slope, axis=0)

                    # CASE A sitting at the stop, then gone without a trace
                    # determined by [d is <100, doesn't change e.g. slope = 0 ]
                    # (0, 50) ***
                    # (1, 50)
                    # (2, 50)
                    # (3, 50)
                    if slope_avg == 0:
                        arrival_time = position_list[0].timestamp
                        case_frequencies['caseA'] += 1
                        print ('caseA {a}'.format(a=arrival_time))

                    # CASE B approaches, then vanishes
                    # determined by [d is decreasing, slope is always negative]
                    # (0, 400)
                    # (1, 300)
                    # (2, 200)
                    # (3, 50) ***
                    elif slope_avg < 0:
                        arrival_time = position_list[-1].timestamp
                        case_frequencies['caseB'] += 1
                        print ('caseB {a}'.format(a=arrival_time))

                    # CASE C appears, then departs
                    # determined by [d is increasing, slope is always positive]
                    # (0, 50) ***
                    # (1, 100)
                    # (2, 200)
                    # (3, 300)
                    elif (slope_avg > 0):
                        arrival_time = position_list[0].timestamp
                        case_frequencies['caseC'] += 1
                        print ('caseC {a}'.format(a=arrival_time))

                    # CASE E boomerang
                    # already arrived at this stop on this trip and now passing by again, this is closest stop on another leg
                    # (e.g. 87 going down the hill after palisade)
                    # these OUGHT to be filtered out by the 'arrival_flags'

                    # OLD CASE D
                    #
                    # elif len(position_list) > 1:
                    #
                    #     # polyfit the line
                    #
                    #     try: # quadratic
                    #         z_quad = np.polyfit(approach_array[:, 0], approach_array[:, 1], 2)
                    #         print(('quad {a}x2 + {b}x + {c}').format(a=z_quad[0], b=z_quad[1], c=z_quad[2]))
                    #     except: # line
                    #         z_line = np.polyfit(approach_array[:, 0], approach_array[:, 1], 1)
                    #         print(('line {a}x + {b}').format(a=z_line[0], b=z_line[1]))
                    #
                    #
                    #
                    #     # if the coefficient on x2 is positive, we are concave up and this is definitely a CASE D:
                    #     if z.quad[0] > 0:
                    #         case_frequencies['caseD'] += 1
                    #
                    #         # now lets find the minimum of the fitted curve
                    #         # using https://nagordon.github.io/mechpy/Curve_fitting_and_Optimization_with_python.html
                    #
                    #         y  = np.poly1d(z_quad)
                    #         xguess = 1 # per above chart todo need to figure how to iterate here?
                    #         y_min = scipy.optimize.minimize(y, xguess)
                    #
                    #         # and then figure out which value element in the approach_array it is closest to
                    #         # closest to approach_array[:, 0]
                    #
                    #         print('caseD')


        print (case_frequencies)
        print ('\n\n')

        session.commit() # sends any updates made above (like setting the arrival flag

        # 4
        # update the database
        # get a session
        #
        # add position_update to the session as table update
        # log the arrival_timestamp for corresponding ScheduledStop
        # session.commit()
