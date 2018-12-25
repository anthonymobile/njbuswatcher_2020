# args = source, route

parser = argparse.ArgumentParser()
parser.add_argument('-s', '--source', dest='source', default='nj', help='source name')
parser.add_argument('-r', '--route', dest='route', required=True, help='route number')

args = parser.parse_args()

from .lib import BusAPI
from .lib import DataBases
from .lib import Localizer

# 1 fetch all bsues on route currently
buses = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data(args.source,'buses_for_route',route=args.route))


# 2 localize them to nearest stop and log to db
session = DataBases.BusPosition.get_session()
for bus in buses:
    current_position = Localizer.get_nearest _stop(bus) # todo REWRITE LOCALIZER TO TAKE A SINGLE BUS INSTANCE AS INPUT AND RETURN IT as a POSITTION
    # todo REWRITE LOCALIZER TO TAKE A SINGLE BUS INSTANCE AS INPUT AND RETURN IT as a POSITTION
    # database_queue(current_position)
# session.database_write, close, flush


# 3 make sure there is a Trip and ScheduledStops for each bus observed
# and update arrival log
for bus in buses:
    # a. check if there's a Trip entry
        # no?
            # getRoutePoints
            # create a ScheduledStop for each listed stop
                # trip_id = v_run_date
                # arrival_position_id = null
            # then, continue to #yes
        # yes
            # for any stop that has observations but not a logged arrival,
            # if d has reached a min and started to increase again -- write the min as the arrival
