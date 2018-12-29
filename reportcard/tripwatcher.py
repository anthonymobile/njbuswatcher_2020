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

    ##############################################
    #
    #   todo UPDATE SCHEDULED STOPS FOR CURRENT TRIPS
    #
    ##############################################

    # loop over list of trips in this position grab
    #for trip in triplist:

        # identify all stops that have new positions
        # result = session.query(ScheduledStops).filter(DataBases.ScheduledStops.trip_id.in_(trip_list))

        # see if any buses have arrived
        # loop over each stop
        # for stop in result:
            # for run in runlist where stopid = stopid?
            # get all the positions for the current run, sort by ascending timestamp
                # 3 or 4 assignment methods
                # 1 - if distance_to_stop has a minumum and has started to increase again
                # 2 - saw it arrive but not depart
                # 3 - saw it depart but not arrive
                # 4 - something else
                # update: SCheduledStop record with an arrival time
                # update: BusPosition record as an arrival
                # add to db session
    # session.common()
