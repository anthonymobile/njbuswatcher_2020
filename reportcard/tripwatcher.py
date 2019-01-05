import argparse, itertools
import numpy as np

# args = source, route
parser = argparse.ArgumentParser()
parser.add_argument('-s', '--source', dest='source', default='nj', help='source name')
parser.add_argument('-r', '--route', dest='route', required=True, help='route number')

args = parser.parse_args()

from lib import BusAPI, Localizer

from lib import DataBases as db

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


    # for each trip
    for trip in triplist:

        print ('\n')
        print(('analyzing trip {a}... arrival candidates on current route:').format(a=trip))

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

        for bus in arrival_candidates:
            print (('stop_id {a}  distance_to_stop {b:.0f} timestamp {c} ').format(c=bus.timestamp, a=bus.stop_id, b=bus.distance_to_stop))

        # groupby stop_id
        position_groups = [list(g) for key, g in itertools.groupby(arrival_candidates, lambda x: x.stop_id)]


        # now loop over the position_groups (except for last one which is current but location) and see if we can assign an arrival time

        for x in range (len(position_groups)-1):
            position_list = position_groups[x]

            # 1 create array (n, distance) for these BusPositions

            approach_array=np.array([])
            for x in range(len(position_list)):
                np.append(approach_array, (x,position_list[x].distance_to_stop))

            print ('\n')
            print (position_list)
            print (approach_array)


            # OVERALL ASSIGNMENT WORKFLOW ALGORITHM

            # create an array to hold the histogram of case frequencies observed (so we can go back later and see which Cases need the most work
            case_frequencies={'caseA':0,'caseB':0,'caseC':0,'caseD':0,}

            # 0 for each trip
            # 0 select all the BusPositions (observed positions, a/k/a breadcrumbs) that are near ScheduledStops that don't have an arrival assigned yet
            # 0 break them into position_lists --- grouped by stop = the breadcrumbs for a single vehicle on a single trip making its approach to a single stop


            # 1 calculate classification metrics

            # calculate slope with numpyapproach_array_np = np.array(approach_array)
            slope = np.diff(approach_array, axis=0)[:, 1]
            acceleration = np.diff(slope, axis=0)
            print (slope)
            print (acceleration)

            avg_slope = np.mean(slope)
            avg_acceleration = np.mean(acceleration)

            # distance_to_stop = done already
            # distance_to_stop/dt = velocity (1st derviative) --> can tell us if the bus is getting closer or further away from stop
            # acceleration = (2nd derviative) --> can tell us if ... TK


            # 2 classify the approach as one of N types

            # CASE A sitting at the stop, then gone without a trace
            # determined by [d is <100, doesn't change e.g. slope = 0 ]
            # (0, 50) ***
            # (1, 50)
            # (2, 50)
            # (3, 50)
            if slope == 0:
                arrival_time = position_list[0].distance_from_stop
                case_frequencies['caseA'] += 1

            # CASE B approaches, then vanishes
            # determined by [d is decreasing, slope is always negative]
            # (0, 400)
            # (1, 300)
            # (2, 200)
            # (3, 50) ***
            elif (slope < 0):
                arrival_time = position_list[:-1].distance_from_stop
                case_frequencies['caseB'] += 1

            # CASE C appears, then departs
            # determined by [d is increasing, slope is always positive]
            # (0, 50) ***
            # (1, 100)
            # (2, 200)
            # (3, 300)
            elif (slope > 0):
                arrival_time = position_list[0].distance_from_stop
                case_frequencies['caseC'] += 1



            # CASE D approach, stop, depart
            # determined by [d is decreasing, slope is negative, then inverts and d is decreasing, slope is increasing, assign to point of lowest d]
            # (0, 200)
            # (1, 100) ***
            # (2, 200)
            # (3, 300)
            # ASSIGNMENT
            # arrival_time = (1)


            elif (slope > 0):

                # polyfit the line
                z = np.polyfit(approach_array[:,0],approach_array[:,1])

                # is it convex up?
                # where is the min? that's our arrival time
                # arrival_time = position_list[0].distance_from_stop

                case_frequencies['caseD'] += 1


            # CASE E boomerang
                # already arrived at this stop on this trip and now passing by again, this is closest stop on another leg
                # (e.g. 87 going down the hill after palisade)
                # these OUGHT to be filtered out by the 'arrival_flags'


            # 3
                # check all ScheduledStops with positions for arrival_flag and interpolate any missing ones
                # can we do it with scipy?



            # 4
                # update related tables

                # 4 update objects
                # 4a flag BusPosition.arrival_flag for record where trip_id=trip and TK=TK?

                # 4b log the arrival_timestamp for paid ScheduledStop
                # position_list[1].arrival_timestamp = arrival_time # todo this updates automagically via SQLalchemy ORM?

        # session.commit()
