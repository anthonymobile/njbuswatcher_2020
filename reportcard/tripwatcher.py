import argparse, sys

# args = source, route
parser = argparse.ArgumentParser()
parser.add_argument('-s', '--source', dest='source', default='nj', help='source name')
parser.add_argument('-r', '--route', dest='route', required=True, help='route number')

args = parser.parse_args()

from lib import BusAPI, Localizer

from lib import DataBases as db

import time
while True:
    delay = 15
    print (('Please wait {a} seconds for next run...').format(a=delay))
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

    #
    #
    # **************** WORKING UP TO HERE ************************
    #
    #


    ##############################################
    #
    #   ASSIGN ARRIVALS
    #
    ##############################################


    # for each trip
    for trip in triplist:

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
            print (('trip {a} bus {b} timestamp {c} stop_id {d} distance_to_stop {e:.0f}').format(a=bus.trip_id, b=bus.id, c=bus.timestamp, d=bus.stop_id, e=bus.distance_to_stop))

        # groupby stop_id
        import itertools
        print ('chicken')
        position_groups = [list(g) for key, g in itertools.groupby(arrival_candidates, lambda x: x.stop_id)]

        # loop over the position_groups and see if we can assign an arrival time



        print ('halt')


    #
    #     for stop, position in arrival_candidates:
    #
    #         # determine if we are ready to assign one of the arrival_candidates as the arrival
    #
    #
    #         position_list = # jsut the posititions for the stop we are working on
    #
    #
    #         # create an approach_array for these BusPositions
    #
    #         # 1 create array (n, distance, slope)
    #         approach_array=[]
    #
    #         for i in range(len(position_list)-1):
    #
    #             # calculate slope
    #             x1=i
    #             x2=i+1
    #             y1=int(position_list[i][0].distance_to_stop) #pick first of tupled join query response
    #             y2=int(position_list[i+1][0].distance_to_stop) # the next in the list
    #             slope = ((y2 - y1) / (x2 - x1))
    #             approach_array.append((i,position_list[i][0].distance_to_stop,slope))
    #
    #         print (approach_array)
    #
    #         # if n == len(position_list):  # last loop
    #         #     approach_array.append((n, position_list[i][0].distance_to_stop, None))
    #         #     break
    #         # else:
    #
    #         # (0, 400, slope)
    #         # (1, 200, slope)
    #         # (2, 100, slope)
    #         # (3, 300, slope)
    #
    #
    #         # 2 classify/assign
    #
    #         # possible cases (easiest to hardest)
    #
    #         # CASE A sitting at the stop, then vanishes
    #         # determined by [d is low, doesn't change much]
    #         # (0, 50) ***
    #         # (1, 50)
    #         # (2, 50)
    #         # (3, 50)
    #         # ASSIGNMENT
    #         # discard OR
    #         # arrival_time = (0)
    #
    #         # CASE B1 approaches, then vanishes
    #         # determined by [d is decreasing, slope is negative]
    #         # (0, 400)
    #         # (1, 300)
    #         # (2, 200)
    #         # (3, 50) ***
    #         # ASSIGNMENT
    #         # arrival_time = (3)
    #
    #
    #         # CASE B2 appears, then departs
    #         # determined by [d is increasing, slope is negative]
    #         # (0, 50) ***
    #         # (1, 100)
    #         # (2, 200)
    #         # (3, 300)
    #         # ASSIGNMENT
    #         # arrival_time = (3)
    #
    #         # CASE C approach, stop, depart
    #         # determined by [d is decreasing, slope is negative, then inverts and d is decreasing, slope is increasing, assign to point of lowest d]
    #         # (0, 200)
    #         # (1, 100) ***
    #         # (2, 200)
    #         # (3, 300)
    #         # ASSIGNMENT
    #         # arrival_time = (1)
    #
    #         # CASE D boomerang
    #         # already arrived at this stop on this trip and now passing by again, this is closest stop on another leg (e.g. 87 going down the hill after palisade)
    #
    #         # CASE E tk
    #
    #
    #         # 3 update objects
    #         # 3a flag BusPosition.arrival_flag for record where trip_id=trip and TK=TK?
    #
    #         # 3b log the arrival_timestamp for paid ScheduledStop
    #         # position_list[1].arrival_timestamp = arrival_time # todo this updates automagically via SQLalchemy ORM?
    #
    #
    # # session.commit()
