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
    delay = 5
    print (('Please wait {a} seconds for first run...').format(a=delay))
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

    # log the localized positions to the database
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
                print ('.')

                session = db.Trip.get_session()
                session.add(trip)
                session.commit()

            # otherwise nothing
            else:
                pass

    ##############################################
    #
    #   todo UPDATE SCHEDULED STOPS FOR CURRENT TRIPS
    #
    ##############################################

    # loop over all the trips we see right now
    for trip in triplist:

        # todo how deal with trip/run # not being unique each day? (look across data see how pervasive this problem is) -- e.g. run #s being reused on the same route in same day at different times -- though odds are low same v and run will appear together?

        # extract all the stops for this trip that do not have an arrival logged
        print (('trip {a}').format(a=trip))
        stoplist = session.query(db.ScheduledStop)\
            .filter(db.ScheduledStop.trip_id == trip) \
            .filter(db.ScheduledStop.arrival_timestamp == None) \
            .all()

        # loop over all the stops
        # todo could probably avoid the double for loop by doing just this query with a join between ScheduledStops and BusPosition
        for stop in stoplist:

            # extract all positions seen near this stop
            position_list = session.query(db.BusPosition, db.ScheduledStop) \
                .join(db.ScheduledStop) \
                .filter(db.BusPosition.trip_id == trip) \
                .filter(db.BusPosition.stop_id == stop.stop_id) \
                .filter(db.ScheduledStop.arrival_timestamp == None) \
                .order_by(db.BusPosition.timestamp.asc()) \
                .all()

            # now process position_list to figure out

            # 1 scan

            # 2 classify/assign

            # possible cases (easiest to hardest)
            # a stop only -- d is low, 1 or more sightings at stop
            # b approach or depart only -- hill - d rises or falls only
            # c approach and depart -- saddle -- d starts high, falls then rises again
            # d boomerang -- already arrived at this stop on this trip and now passing by again, this is closest stop on another leg (e.g. 87 going down the hill after palisade)
            # e TK
            # f TK
            # g TK baddata

            # 3 update objects
            # 3a flag BusPosition.arrival_flag for record where trip_id=trip and TK=TK?
            # 3b log the arrival_timestamp for ScheduledStop where trip_id=trip


            # add to db session
    # session.commit()
