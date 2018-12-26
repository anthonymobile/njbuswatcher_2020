import datetime, sys, argparse

# args = source, route
parser = argparse.ArgumentParser()
parser.add_argument('-s', '--source', dest='source', default='nj', help='source name')
parser.add_argument('-r', '--route', dest='route', required=True, help='route number')

args = parser.parse_args()

from lib import BusAPI
from lib import DataBases
from lib import Localizer

# database initialization
trip_session = DataBases.Trip.get_session()
stop_session = DataBases.ScheduledStop.get_session()
position_session = DataBases.BusPosition.get_session()

print ('Starting...')

# 1 fetch all buses on route currently
# buses = a list of Bus objects
print ('Fetching buses...')
buses = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data(args.source,'buses_for_route',route=args.route))
print ('Got buses...')

# 2 localize them to nearest stop and log to db
# bus_positions = list of BusPosition objects
print ('Localizing buses...')
bus_positions = Localizer.get_nearest_stop(buses)
print ('Localized buses...')
sys.exit()

# 3 log positions to trips
for bus in bus_positions:

    # check if there's a Trip where trip id = v_run_yyyymmdd
    trip_id = ('{v}_{run}_{dt}').format(bus=bus.v,run=bus.run,dt=datetime.datetime.today().strftime('%Y-%m-%d'))

    # if there isn't a trip already
    if not trip_session.query(DataBases.Trip).filter(DataBases.Trip.trip_id == trip_id).all():

        trip = DataBases.Trip(bus.v, bus.run) # todo create the Trip object
        routes = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data(source,'buses_for_route',route=args.route)) # todo fill it up with stops from the right service/trip/run with

        stoplist = []
        for stop in routes.path.TK:
            if isinstance(Stop):
                stop = DataBases.Trip(tk,tk) # todo create the Trip object
                # append it to a list of stops
        stop_session.bulk_save_objects(stoplist)

        # bus.trip_id = trip_id
        #

    else:
        bus.trip_id = trip_id

# todo not sure if the above is actually changing anything (bus.trip_id -- the list isn't mutable, but the objects inside it are?
# write updated bus_positions (with trip_id) to db

position_session.bulk_save_objects(bus_positions)

# # 4 now process all the stops we've touched and update arrival log
# # todo this can probably live inside one of the loops aboe near the end
# # but want to make sure all the buses have been processed first?
#
# for bus in bus_positions: # loop over buses on route now
#     for runs in bus_positions : # filter by runs current observed on route now
#         for v in bus_positions: # filter by vehicles current observed on route now
#             get all of the positions for this run, v, ,yyyymmdd, bus.stop_id AND sort by time ascending
#             if distance_to_stop has a minumum and has started to increase again
#             update: SCheduledStop record with an arrival time
#             update: BusPosition record as an arrival




