import time, argparse

# args = source, route
parser = argparse.ArgumentParser()
parser.add_argument('-s', '--source', dest='source', default='nj', help='source name')
parser.add_argument('-r', '--route', dest='route', required=True, help='route number')

args = parser.parse_args()

from lib import BusAPI, DataBases, Localizer

##############################################
#
#   FETCH AND LOCALIZE CURRENT POSITIONS
#
##############################################

print ('trip_id\t\t\t\t\tv\t\trun\tstop_id\tdistance_to_stop (feet)')


# 1 fetch all buses on route currently
# buses = a list of Bus objects

try:
    buses = BusAPI.parse_xml_getBusesForRoute(BusAPI.get_xml_data(args.source,'buses_for_route',route=args.route))
except OSError as e:
    continue #todo need to catch rest of errors when network is down

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

b = bus_positions[0][0]
print (('t{a}\t\t{b}\t{c}\t{d}\t{e:.0f}').format(a=b.trip_id,b=b.id,c=b.run,d=b.stop_id,e=b.distance_to_stop))

##############################################
#
#   ASSIGN AND LOG CURRENT POSITIONS TO TRIPS
#
##############################################

session = DataBases.Trips.get_session()

triplist=[]
# loop over the buses
for bus in bus_positions:

    # check if there's already a corresponding trip record
    trip_id = ('{v}_{run}_{dt}').format(bus=bus.v,run=bus.run,dt=datetime.datetime.today().strftime('%Y%m%d'))

    # # if there isn't a trip already
    if not session.query(Trip).filter(Trip.trip_id == trip_id).all():
        trip = DataBases.Trip(bus.v, bus.run)
    else:
        bus.trip_id = trip_id # todo not sure if the above is actually changing anything (bus.trip_id -- the list isn't mutable, but the objects inside it are?

    # either way, note the current trip
    triplist.append(trip_id)

# todo write updated bus_positions (with trip_id) to db
# position_session.bulk_save_objects(bus_positions)

##############################################
#
#   UPDATE SCHEDULED STOPS FOR CURRENT TRIPS
#
##############################################

for trip in triplist:
    # result = session.query(Trip).filter(Trip.trip_id == trip_id).all()

    # not sure wright # of loops below
    # for bus in bus_positions: # loop over buses on route now
    #     for runs in bus_positions : # filter by runs current observed on route now
    #         for v in bus_positions: # filter by vehicles current observed on route now
    #             get all of the positions for this run, v, ,yyyymmdd, bus.stop_id AND sort by time ascending
    #             if distance_to_stop has a minumum and has started to increase again
    #             update: SCheduledStop record with an arrival time
    #             update: BusPosition record as an arrival




