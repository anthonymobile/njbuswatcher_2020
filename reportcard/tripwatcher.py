import argparse, sys

# args = source, route
parser = argparse.ArgumentParser()
parser.add_argument('-s', '--source', dest='source', default='nj', help='source name')
parser.add_argument('-r', '--route', dest='route', required=True, help='route number')

args = parser.parse_args()

from lib import BusAPI, DataBases, Localizer


import time
while True:
    time.sleep(30)

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
    session = DataBases.BusPosition.get_session()
    for group in bus_positions:
        for bus in group:
            session.add(bus)
    session.commit()

    # 3 generate some diagnostic output of what we just tracked
    print ('trip_id\t\t\t\t\tv\t\trun\tstop_id\tdistance_to_stop (feet)')


    # b = bus_positions[0][0]
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
            result = session.query(DataBases.Trip).filter(DataBases.Trip.trip_id == bus.trip_id).first()

            # if there is no Trip record yet, create one
            if result is None:
                trip = DataBases.Trip(args.source, args.route, bus.id, bus.run)
                print ('.')

                session = DataBases.Trip.get_session()
                session.add(trip)
                session.commit()

            # otherwise nothing
            else:
                pass

    # write to the db


    ##############################################
    #
    #   todo UPDATE SCHEDULED STOPS FOR CURRENT TRIPS
    #
    ##############################################

    # for trip in triplist:
        # result = session.query(Trip).filter(Trip.trip_id == trip_id).all()

        # not sure right # of loops below
        # for bus in bus_positions: # loop over buses on route now
        #     for runs in bus_positions : # filter by runs current observed on route now
        #         for v in bus_positions: # filter by vehicles current observed on route now
        #             get all of the positions for this run, v, ,yyyymmdd, bus.stop_id AND sort by time ascending
        #             if distance_to_stop has a minumum and has started to increase again
        #             update: SCheduledStop record with an arrival time
        #             update: BusPosition record as an arrival




