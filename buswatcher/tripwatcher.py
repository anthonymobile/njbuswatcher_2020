#
# usage:
# (statewide)                                           tripwatcher.py --statewide
# (only routes in defined collections)                  tripwatcher.py
#

import argparse
import time

from buswatcher.lib.RouteScan import RouteScan

from buswatcher.lib.RouteConfig import load_system_map, flush_system_map,maintenance_check
from buswatcher.lib.CommonTools import timeit
#
# class RouteScan: # moved to RouteScan.py # todo 1 remove this large block
#
#     # @timeit
#     def __init__(self, system_map, route, statewide):
#
#         # apply passed parameters to instance
#         self.route = route
#         self.statewide = statewide
#         try:
#             self.route_map_xml=system_map.single_route_xml(self.route)
#         except:
#             self.route_map_xml={'xml':''}
#
#         # create database connection
#         self.db = SQLAlchemyDBConnection()
#
#         # initialize instance variables
#         self.buses = []
#         self.trip_list = []
#
#         #  populate route basics from config
#         system_map=load_system_map()
#
#
#         # generate scan data and results
#         with SQLAlchemyDBConnection() as self.db:
#             self.fetch_positions()
#             self.parse_positions(system_map)
#             self.localize_positions(system_map)
#             self.interpolate_missed_stops()
#             self.assign_positions()
#
#
#     def fetch_positions(self):
#
#         if self.statewide is False:
#
#             self.buses = BusAPI.parse_xml_getBusesForRoute(BusAPI.get_xml_data('nj', 'buses_for_route', route=self.route))
#             # sys.stdout.write('\rfetched route' + str(self.route) + '... ')
#
#             self.clean_buses()
#
#         elif self.statewide is True:
#
#             self.buses = BusAPI.parse_xml_getBusesForRouteAll(BusAPI.get_xml_data('nj', 'all_buses'))
#             print('\rfetched ' + str(len(self.buses)) + ' buses...')
#
#             self.clean_buses()
#
#         return
#
#
#     def clean_buses(self):
#         # CLEAN buses not actively running routes (e.g. letter route codes)
#         buses_cleaned=[]
#         for bus in self.buses:
#             try:
#                 int(bus.rt)
#                 buses_cleaned.append(bus)
#             except:
#                 pass
#         self.buses = buses_cleaned
#
#         return
#
#
#     def parse_positions(self,system_map):
#
#         with self.db as db:
#
#             # PARSE trips, create missing trip records first, to honor foreign key constraints
#             # sys.stdout.write('parsing...')
#             for bus in self.buses:
#                 bus.trip_id = ('{id}_{run}_{dt}').format(id=bus.id, run=bus.run,dt=datetime.datetime.today().strftime('%Y%m%d'))
#                 self.trip_list.append(bus.trip_id)
#                 result = db.session.query(Trip).filter(Trip.trip_id == bus.trip_id).first()
#
#                 if result is None:
#                     trip_id = Trip('nj', system_map, bus.rt, bus.id, bus.run, bus.pid)
#                     db.session.add(trip_id)
#                 else:
#                     continue
#                 db.__relax__()  # disable foreign key checks before...
#                 db.session.commit()  # we save the position_log.
#             return
#
#
#     def localize_positions(self,system_map):
#
#             with self.db as db:
#
#                 try:
#                     # LOCALIZE
#                     if self.statewide is False:
#                         bus_positions = Localizer.get_nearest_stop(system_map, self.buses, self.route)
#                         for group in bus_positions:
#                             for bus in group:
#                                 db.session.add(bus)
#
#                         db.__relax__()  # disable foreign key checks before commit
#                         db.session.commit()
#
#                     elif self.statewide is True:
#                         # find all the routes
#                         statewide_route_list = [bus.rt for bus in self.buses]
#                         # loop over each route
#                         for r in statewide_route_list:
#                             # print('localizing routes %a').format(a=r)
#                             bus_positions = Localizer.get_nearest_stop(system_map, self.buses, r)
#                             for group in bus_positions:
#                                 for bus in group:
#                                     db.session.add(bus)
#                             db.__relax__()  # disable foreign key checks before commit
#                             db.session.commit()
#
#
#
#                 except (IntegrityError) as e:
#                     error_count = + 1
#                     print(e + 'mysql integrity error #' + error_count)
#
#             return
#
#
#     def assign_positions(self):
#
#         with self.db as db:
#
#             # ASSIGN TO NEAREST STOP
#             for trip_id in self.trip_list:
#
#                 # load the trip card for reference
#                 scheduled_stops = db.session.query(Trip, ScheduledStop) \
#                     .join(ScheduledStop) \
#                     .filter(Trip.trip_id == trip_id) \
#                     .all()
#
#                 # select all the BusPositions on ScheduledStops where there is no arrival flag yet
#                 arrival_candidates = db.session.query(BusPosition) \
#                     .join(ScheduledStop) \
#                     .filter(BusPosition.trip_id == trip_id) \
#                     .filter(ScheduledStop.arrival_timestamp == None) \
#                     .order_by(BusPosition.timestamp.asc()) \
#                     .all()
#
#                 # split them into groups by stop
#                 position_groups = [list(g) for key, g in itertools.groupby(arrival_candidates, lambda x: x.stop_id)]
#
#                 # iterate over all but last one (which is stop bus is currently observed at)
#                 for x in range(len(position_groups) - 1):
#
#                     # slice the positions for the xth stop
#                     position_list = position_groups[x]
#
#                     # GRAB THE STOP RECORD FROM DB FOR UPDATING ARRIVAL INFO
#                     stop_to_update = db.session.query(ScheduledStop, BusPosition) \
#                         .join(BusPosition) \
#                         .filter(ScheduledStop.trip_id == position_list[0].trip_id) \
#                         .filter(ScheduledStop.stop_id == position_list[0].stop_id) \
#                         .all()
#
#                     ##############################################
#                     #   ONE POSITION
#                     #   if we only have one observation and since
#                     #   this isn't the current stop, then we've
#                     #   already passed it and can just assign it
#                     #   as the arrival
#                     ##############################################
#
#                     if len(position_list) == 1:
#                         arrival_time = position_list[0].timestamp
#                         position_list[0].arrival_flag = True
#                         case_identifier = '1a'
#                         approach_array = np.array([0, position_list[0].distance_to_stop])
#
#                     ##############################################
#                     #   TWO POSITIONS
#                     #   calculate the slope between the two points
#                     #   and assign to CASE A,B, or C
#                     #   arrival is either the 1st observed position
#                     #   or the 2nd
#                     ##############################################
#
#                     elif len(position_list) == 2:
#
#                         # create and display approach array
#                         points = []
#                         for y in range(len(position_list)):
#                             points.append((y, position_list[y].distance_to_stop))
#                         approach_array = np.array(points)
#
#                         # calculate classification metrics
#                         slope = np.diff(approach_array, axis=0)[:, 1]
#                         acceleration = np.diff(slope, axis=0)
#                         slope_avg = np.mean(slope, axis=0)
#
#                         # CASE A sitting at the stop, then gone without a trace
#                         # determined by [d is <100, doesn't change e.g. slope = 0 ]
#                         # (0, 50)  <-----
#                         # (1, 50)
#                         if slope_avg == 0:
#                             arrival_time = position_list[0].timestamp
#                             position_list[0].arrival_flag = True
#                             case_identifier = '2a'
#
#                         # CASE B approaches, then vanishes
#                         # determined by [d is decreasing, slope is always negative]
#                         # (0, 400)
#                         # (1, 300) <-----
#                         elif slope_avg < 0:
#                             arrival_time = position_list[-1].timestamp
#                             position_list[-1].arrival_flag = True
#                             case_identifier = '2b'
#
#                         # CASE C appears, then departs
#                         # determined by [d is increasing, slope is always positive]
#                         # (0, 50)  <-----
#                         # (1, 100)
#                         elif slope_avg > 0:
#                             arrival_time = position_list[0].timestamp
#                             position_list[0].arrival_flag = True
#                             case_identifier = '2c'
#
#                     ##############################################
#                     #   THREE OR MORE POSITIONS
#                     ##############################################
#
#                     elif len(position_list) > 2:
#
#                         # create and display approach array
#                         # print(('\tapproaching {b}').format(a=trip_id, b=position_list[0].stop_id))
#                         points = []
#                         for y in range(len(position_list)):
#                             points.append((y, position_list[y].distance_to_stop))
#                         approach_array = np.array(points)
#                         # for point in approach_array:
#                         # print(('\t\t {a:.0f} distance_to_stop {b}').format(a=point[0], b=point[1]))
#
#                         # calculate classification metrics
#                         slope = np.diff(approach_array, axis=0)[:, 1]
#                         acceleration = np.diff(slope, axis=0)
#                         slope_avg = np.mean(slope, axis=0)
#
#                         try:
#                             # CASE A
#                             if slope_avg == 0:
#                                 arrival_time = position_list[0].timestamp
#                                 position_list[0].arrival_flag = True
#                                 case_identifier = '3a'
#                                 # plot_approach(trip_id, np.array([0, position_list[0].distance_to_stop]), case_identifier)
#
#                             # CASE B
#                             elif slope_avg < 0:
#                                 arrival_time = position_list[-1].timestamp
#                                 position_list[-1].arrival_flag = True
#                                 case_identifier = '3b'
#                                 # plot_approach(trip_id, np.array([0, position_list[-1].distance_to_stop]), case_identifier)
#
#                             # CASE C
#                             elif slope_avg > 0:
#                                 arrival_time = position_list[0].timestamp
#                                 position_list[0].arrival_flag = True
#                                 case_identifier = '3c'
#                                 # plot_approach(trip_id, np.array([0, position_list[0].distance_to_stop]), case_identifier)
#
#                             # to do add 2 `Boomerang buses (Case D)`
#
#                         except:
#                             pass
#
#                     # catch errors for unassigned 3+-position approaches
#                     # to do 2 debug approach assignment: 3+ position seems to still be having problems...
#                     try:
#                         stop_to_update[0][0].arrival_timestamp = arrival_time
#                     except:
#                         pass
#
#             db.session.commit()
#
#             return
#
#
#     def interpolate_missed_stops(self):
#
#         # INTERPOLATE ARRIVALS AT MISSED STOPS
#         # to do 2 add Interpolate+log missed stops
#         # interpolates arrival times for any stops in between arrivals in the trip card
#         # theoretically there shouldn't be a lot though if the trip card is correct
#         # since we are grabbing positions every 30 seconds.)
#
#         return

@timeit
def main_loop(system_map):

    if args.statewide is False:
        for collection,collection_description in system_map.collection_descriptions.items():
            for r in collection_description['routelist']:
                try:
                    RouteScan(system_map, r, args.statewide)
                except:
                    pass
    elif args.statewide is True:
        RouteScan(system_map, 0, args.statewide)
    return

if __name__ == "__main__":


    flush_system_map()
    system_map=load_system_map()
    # route_definitions, grade_descriptions, collection_descriptions = load_config()
    # route_definitions = route_definitions['route_definitions'] # ignore the ttl, last_updated key:value pairs

    # maintenance check
    maintenance_check(system_map)

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--statewide', dest='statewide', action='store_true', help='Watch all active routes in NJ. (requires lots of CPU).')
    args = parser.parse_args()

    if args.statewide is False:
        print('running in collections mode (watch all routes in all collections)')
    elif args.statewide is True:
        print('running in statewide mode (watch all routes in NJ)')

    run_frequency = 60 # seconds
    time_start=time.monotonic()

    while True:
        scan = main_loop(system_map)
        print('***sleeping***')
        time.sleep(run_frequency - ((time.monotonic() - time_start) % 60.0))  # sleep remainder of the 60 second loop




