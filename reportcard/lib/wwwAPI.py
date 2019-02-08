import pickle
import datetime
import pandas as pd
import geojson

from sqlalchemy import inspect

import lib.BusAPI as BusAPI
from lib.DataBases import DBConfig, SQLAlchemyDBConnection, Trip, BusPosition, ScheduledStop

from route_config import reportcard_routes, grade_descriptions

# common functions
def timestamp_fix(data): # trim the microseconds off the timestamp and convert it to datetime format
    data['timestamp'] = data['timestamp'].str.split('.').str.get(0)
    data['timestamp'] = pd.to_datetime(data['timestamp'],errors='coerce')
    # data = data.set_index(pd.DatetimeIndex(data['timestamp']))
    data = data.set_index(pd.DatetimeIndex(data['timestamp']), drop=False)
    return data

# convery sqlalchemy query to a dict
# https://stackoverflow.com/questions/1958219/convert-sqlalchemy-row-object-to-python-dict
def object_as_dict(obj):
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}

# geoJSON for citywide map
def citymap_geojson(reportcard_routes):
    points = []
    stops = []
    for i in reportcard_routes:
        routes, coordinate_bundle = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data('nj', 'routes', route=i['route']))
        points_feature = coordinate_bundle['waypoints_geojson']
        stops_feature = coordinate_bundle['stops_geojson']

        points.append(points_feature)
        stops.append(stops_feature)
    map_points = geojson.FeatureCollection(points)
    map_stops = geojson.FeatureCollection(stops)
    return map_points, map_stops


# primary classes
class RouteReport:

    class Path():
        def __init__(self):
            self.name = 'Path'
            self.stops = []
            self.id = ''
            self.d = ''
            self.dd = ''

    def __init__(self, source, route):

        # apply passed parameters to instance
        self.source = source
        self.route = route

        # populate route basics from config
        self.reportcard_routes = reportcard_routes
        self.grade_descriptions = grade_descriptions

        # populate static report card data
        self.routename, self.waypoints_coordinates, self.stops_coordinates, self.waypoints_geojson, self.stops_geojson = self.get_routename(self.route) #todo -- can we eliminate this? redundant -- read it from Trip?
        self.load_route_description()
        self.route_stop_list = self.get_stoplist(self.route)

        # populate live report card data
        self.active_trips, self.active_trips_5 = self.get_activetrips()


    def get_routename(self,route):
        routes, coordinate_bundle = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data(self.source, 'routes', route=route))
        return routes[0].nm, coordinate_bundle['waypoints_coordinates'], coordinate_bundle['stops_coordinates'], coordinate_bundle['waypoints_geojson'], coordinate_bundle['stops_geojson']

    def load_route_description(self):
        for route in self.reportcard_routes:
            if route['route'] == self.route:
                self.frequency = route['frequency']
                self.description_long = route['description_long']
                self.prettyname = route['prettyname']
                self.schedule_url = route['schedule_url']
            else:
                pass
        return

    # gets all stops on all active routes
    def get_stoplist(self, route):
        routes, coordinate_bundle = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data(self.source, 'routes', route=self.route))
        route_stop_list = []
        for r in routes:
            path_list = []
            for path in r.paths:
                stops_points = RouteReport.Path()
                for point in path.points:
                    if isinstance(point, BusAPI.Route.Stop):
                        stops_points.stops.append(point)
                stops_points.id=path.id
                stops_points.d=path.d
                stops_points.dd=path.dd
                path_list.append(stops_points) # path_list is now a couple of Path instances, plus the metadata id,d,dd fields
            route_stop_list.append(path_list)
        return route_stop_list[0] # transpose a single copy since the others are all repeats (can be verified by path ids)


    def get_activetrips(self):

        # query db and load up everything we want to display
        # (basically what's on the approach_dash)

        active_trips = list()

        todays_date = datetime.datetime.today().strftime('%Y%m%d')

        # grab buses on road now and populate trip cards
        buses_on_route = BusAPI.parse_xml_getBusesForRoute(BusAPI.get_xml_data(self.source, 'buses_for_route', route=self.route))
        for b in buses_on_route:
            current_trip = dict()
            trip_id = ('{id}_{run}_{dt}').format(id=b.id, run=b.run, dt=datetime.datetime.today().strftime('%Y%m%d'))

            with SQLAlchemyDBConnection(DBConfig.conn_str) as db:
                # load the trip card
                scheduled_stops = db.session.query(Trip.pid, Trip.trip_id, ScheduledStop.trip_id, ScheduledStop.stop_id, ScheduledStop.stop_name, ScheduledStop.arrival_timestamp) \
                    .join(ScheduledStop) \
                    .filter(Trip.trip_id == trip_id) \
                    .all()
                    #todo sort on something?

                #convert the query
                # active trips is a list, each item contains a dict
                # {'pid': 1634, 'trip_id': '5722_16_20190208', 'stop_id': 20496, 'arrival_timestamp': None}
                current_trip['trip_id'] = trip_id
                current_trip['trip_card'] = list(map(lambda obj: dict(zip(obj.keys(), obj)), scheduled_stops))
                active_trips.append(current_trip)

        # reverse sort on timestamp then take the first 5
        # like https://www.geeksforgeeks.org/ways-sort-list-dictionaries-values-python-using-lambda-function/
        # trying to sort a nested dict?
        print (active_trips[0])

        # https://www.w3resource.com/python-exercises/list/python-data-type-list-exercise-50.php
        my_list = [{'key': {'subkey': 1}}, {'key': {'subkey': 10}}, {'key': {'subkey': 5}}]
        print("Original List: ")
        print(my_list)
        my_list.sort(key=lambda e: e['key']['subkey'], reverse=True)
        print("Sorted List: ")
        print(my_list)


        active_trips.sort(key=lambda x: x['trip_card']['arrival_timestamp'], reverse=True)

        active_trips_5=active_trips[:5]

        return active_trips, active_trips_5




    # pull this from the database based on the Tripid?
    # using with SQLAlchemyDBConnection as db:


    # def generate_bunching_leaderboard(self, period, route):
    #     # generates top 10 list of stops on the route by # of bunching incidents for period
    #     bunching_leaderboard = []
    #     cum_arrival_total = 0
    #     cum_bunch_total = 0
    #     for service in self.route_stop_list:
    #         for stop in service.stops:
    #             bunch_total = 0
    #             arrival_total = 0
    #             report = StopReport(self.route, stop.identity,period)
    #             for (index, row) in report.arrivals_list_final_df.iterrows():
    #                 arrival_total += 1
    #                 if (row.delta > report.bigbang) and (row.delta <= report.bunching_interval):
    #                     bunch_total += 1
    #             cum_bunch_total = cum_bunch_total+bunch_total
    #             cum_arrival_total = cum_arrival_total + arrival_total
    #             bunching_leaderboard.append((stop.st, bunch_total,stop.identity))
    #     bunching_leaderboard.sort(key=itemgetter(1), reverse=True)
    #     bunching_leaderboard = bunching_leaderboard[:10]
    #
    #     # compute grade passed on pct of all stops on route during period that were bunched
    #     try:
    #         grade_numeric = (cum_bunch_total / cum_arrival_total) * 100
    #         for g in self.grade_descriptions:
    #             if g['bounds'][0] < grade_numeric <= g['bounds'][1]:
    #                 self.grade = g['grade']
    #                 self.grade_description = g['description']
    #     except:
    #         self.grade = 'N/A'
    #         self.grade_description = 'Unable to determine grade.'
    #         pass
    #
    #     time_created = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    #     bunching_leaderboard_pickle = dict(bunching_leaderboard=bunching_leaderboard, grade=self.grade,
    #                                        grade_numeric=grade_numeric, grade_description=self.grade_description, time_created=time_created)
    #     outfile = ('data/bunching_leaderboard_'+route+'.pickle')
    #     with open(outfile, 'wb') as handle:
    #         pickle.dump(bunching_leaderboard_pickle, handle, protocol=pickle.HIGHEST_PROTOCOL)
    #     return


    # def load_bunching_leaderboard(self,route):
    #     infile = ('data/bunching_leaderboard_'+route+'.pickle')
    #     with open(infile, 'rb') as handle:
    #         b = pickle.load(handle)
    #     return b['bunching_leaderboard'], b['grade'], b['grade_numeric'], b['grade_description'], b['time_created']

###################################################
#  old ReportCard.py
###################################################
#
#
# import datetime, pickle
# from operator import itemgetter
# import pandas as pd
#
# # database config
# import os
# try:
#     db_state = os.environ['REPORTCARD_PRODUCTION']
#     db_server = '192.168.1.181'
# except:
#     db_server = '127.0.0.1'
#
# # import app libraries
# from . import BusAPI, Localizer
#


# # primary classes
# class RouteReport:
#
#     class Path():
#         def __init__(self):
#             self.name = 'Path'
#             self.stops = []
#             self.id = ''
#             self.d = ''
#             self.dd = ''
#
#     def __init__(self, source, route, reportcard_routes, grade_descriptions): # replace last 2 with **kwargs to make them optional?
#
#         # apply passed parameters to instance
#         self.source = source
#         self.route = route
#         self.reportcard_routes = reportcard_routes
#         self.grade_descriptions = grade_descriptions
#
#         # database initialization
#         self.db = StopsDB.MySQL('buses', 'buswatcher', 'njtransit', db_server, self.route)
#         self.conn = self.db.conn
#         self.table_name = 'stop_approaches_log_' + self.route
#
#         # populate report card data
#         self.routename, self.waypoints_coordinates, self.stops_coordinates, self.waypoints_geojson, self.stops_geojson = self.get_routename(self.route)
#         self.load_route_description()
#         self.route_stop_list = self.get_stoplist(self.route)
#
#     def get_routename(self,route):
#         routedata, waypoints_coordinates, stops_coordinates,waypoints_geojson, stops_geojson = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data(self.source, 'routes', route=route))
#         return routedata[0].nm, waypoints_coordinates, stops_coordinates, waypoints_geojson, stops_geojson
#
#     def load_route_description(self):
#         # for now, grade is coded manually in route_config.py
#         # FUTURE fancier grade calculation based on historical data
#         for route in self.reportcard_routes:
#             if route['route'] == self.route:
#                 self.frequency = route['frequency']
#                 self.description_long = route['description_long']
#                 self.prettyname = route['prettyname']
#                 self.schedule_url = route['schedule_url']
#
#             else:
#                 pass
#         return
#
#     def get_stoplist(self, route):
#         routedata, waypoints_coordinates, stops_coordinates, waypoints_geojson, stops_geojson = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data(self.source, 'routes', route=self.route))
#         route_stop_list = []
#         for r in routedata:
#             path_list = []
#             for path in r.paths:
#                 stops_points = RouteReport.Path()
#                 for point in path.points:
#                     if isinstance(point, BusAPI.Route.Stop):
#                         stops_points.stops.append(point)
#                 stops_points.id=path.id
#                 stops_points.d=path.d
#                 stops_points.dd=path.dd
#                 path_list.append(stops_points) # path_list is now a couple of Path instances, plus the metadata id,d,dd fields
#             route_stop_list.append(path_list)
#         return route_stop_list[0] # transpose a single copy since the others are all repeats (can be verified by path ids)
#
#     def generate_bunching_leaderboard(self, period, route):
#         # generates top 10 list of stops on the route by # of bunching incidents for period
#
#         bunching_leaderboard = []
#
#         cum_arrival_total = 0
#         cum_bunch_total = 0
#
#         for service in self.route_stop_list:
#             for stop in service.stops:
#                 bunch_total = 0
#                 arrival_total = 0
#
#                 report = StopReport(self.route, stop.identity,period)
#                 for (index, row) in report.arrivals_list_final_df.iterrows():
#                     arrival_total += 1
#                     if (row.delta > report.bigbang) and (row.delta <= report.bunching_interval):
#                         bunch_total += 1
#                 cum_bunch_total = cum_bunch_total+bunch_total
#                 cum_arrival_total = cum_arrival_total + arrival_total
#                 bunching_leaderboard.append((stop.st, bunch_total,stop.identity))
#
#         bunching_leaderboard.sort(key=itemgetter(1), reverse=True)
#         bunching_leaderboard = bunching_leaderboard[:10]
#
#         # compute grade passed on pct of all stops on route during period that were bunched
#
#         try:
#             grade_numeric = (cum_bunch_total / cum_arrival_total) * 100
#             for g in self.grade_descriptions:
#                 if g['bounds'][0] < grade_numeric <= g['bounds'][1]:
#                     self.grade = g['grade']
#                     self.grade_description = g['description']
#         except:
#             self.grade = 'N/A'
#             self.grade_description = 'Unable to determine grade.'
#             pass
#
#         time_created = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#
#         bunching_leaderboard_pickle = dict(bunching_leaderboard=bunching_leaderboard, grade=self.grade,
#                                            grade_numeric=grade_numeric, grade_description=self.grade_description, time_created=time_created)
#
#         outfile = ('data/bunching_leaderboard_'+route+'.pickle')
#         with open(outfile, 'wb') as handle:
#             pickle.dump(bunching_leaderboard_pickle, handle, protocol=pickle.HIGHEST_PROTOCOL)
#
#         return
#
#     def load_bunching_leaderboard(self,route):
#
#         infile = ('data/bunching_leaderboard_'+route+'.pickle')
#         with open(infile, 'rb') as handle:
#             b = pickle.load(handle)
#
#         return b['bunching_leaderboard'], b['grade'], b['grade_numeric'], b['grade_description'], b['time_created']
#
# class StopReport:
#
#     def __init__(self,route,stop,period):
#
#         # apply passed parameters to instance
#         self.route=route
#         self.stop=stop
#         self.period=period
#
#         # database initialization
#         self.db = StopsDB.MySQL('buses', 'buswatcher', 'njtransit', db_server,  self.route)
#         self.conn = self.db.conn
#         self.table_name = 'stop_approaches_log_' + self.route
#
#         # populate stop report data
#         self.arrivals_list_final_df, self.stop_name = self.get_arrivals(self.route,self.stop,self.period)
#       self.hourly_frequency =  get_hourly_frequency(route, stop, period)
#
#         # constants
#         self.bunching_interval = datetime.timedelta(minutes=3)
#         self.bigbang = datetime.timedelta(seconds=0)
#
#
#     # New_Localizer
#     def get_arrivals(self, route, stop, period):
#
#         source = 'nj'
#         try:
#             bus_data = BusAPI.parse_xml_getBusesForRoute(BusAPI.get_xml_data(source, 'buses_for_route', route=route))
#             arrivals_list_final_df = Localizer.find_nearest_stops(position_log=bus_data, route='87')
#             stop_name = arrivals_list_final_df['stop_name'].iloc[0]
#
#         except:
#             arrivals_list_final_df = \
#                 pd.DataFrame( \
#                     columns=['pkey', 'pt', 'rd', 'stop_id', 'stop_name', 'v', 'timestamp', 'delta'], \
#                     data=[['0000000', '3', self.route, self.stop, 'N/A', 'N/A', datetime.time(0, 1),
#                            datetime.timedelta(seconds=0)]])
#             stop_name = 'N/A'
#             self.arrivals_table_time_created = datetime.datetime.now()
#
#
#         return arrivals_list_final_df, stop_name
#
#     # def get_arrivals(self,route,stop,period):
#     #
#     #     if self.period == "daily":
#     #         final_approach_query = ('SELECT * FROM %s WHERE (rd=%s AND stop_id= %s AND DATE(`timestamp`)=CURDATE() ) ORDER BY timestamp;' % (self.table_name, self.route, self.stop))
#     #     elif self.period == "yesterday":
#     #         final_approach_query = ('SELECT * FROM %s WHERE (rd=%s AND stop_id= %s AND (timestamp >= CURDATE() - INTERVAL 1 DAY AND timestamp < CURDATE())) ORDER BY timestamp;' % (self.table_name, self.route, self.stop))
#     #     elif self.period=="weekly":
#     #         final_approach_query = ('SELECT * FROM %s WHERE (rd=%s AND stop_id= %s AND (YEARWEEK(`timestamp`, 1) = YEARWEEK(CURDATE(), 1))) ORDER BY timestamp;' % (self.table_name, self.route, self.stop))
#     #     elif self.period=="history":
#     #         final_approach_query = ('SELECT * FROM %s WHERE (rd=%s AND stop_id= %s) ORDER BY timestamp;' % (self.table_name, self.route, self.stop))
#     #     else:
#     #         raise RuntimeError('Bad request sucker!')
#     #
#     #     # get data and basic cleanup
#     #     df_temp = pd.read_sql_query(final_approach_query, self.conn) # arrivals table and deltas are all re-generated on the fly for every view now -- easier, but might lead to inconsistent/innaccurate results over time?
#     #     df_temp = df_temp.drop(columns=['cars', 'consist', 'fd', 'm', 'name', 'rn', 'scheduled'])
#     #     df_temp = timestamp_fix(df_temp)
#     #
#     #     # split final approach history (sorted by timestamp) at each change in vehicle_id outputs a list of dfs -- per https://stackoverflow.com/questions/41144231/python-how-to-split-pandas-dataframe-into-subsets-based-on-the-value-in-the-fir
#     #     final_approach_dfs = [g for i, g in df_temp.groupby(df_temp['v'].ne(df_temp['v'].shift()).cumsum())]
#     #
#     #     try:
#     #         # take the last V(ehicle) approach in each df and add it to final list of arrivals
#     #         arrivals_list_final_df = pd.DataFrame()
#     #         for final_approach in final_approach_dfs:  # iterate over every final approach
#     #             arrival_insert_df = final_approach.tail(1)  # take the last observation
#     #             arrivals_list_final_df = arrivals_list_final_df.append(arrival_insert_df)  # insert into df
#     #
#     #         # calc interval between last bus for each row, fill NaNs
#     #         arrivals_list_final_df['delta']=(arrivals_list_final_df['timestamp'] - arrivals_list_final_df['timestamp'].shift(1)).fillna(0)
#     #
#     #         # housekeeping ---------------------------------------------------
#     #
#     #         # set stop_name
#     #         stop_name = arrivals_list_final_df['stop_name'].iloc[0]
#     #
#     #         # resort arrivals list
#     #         # arrivals_list_final_df.sort_values("timestamp", inplace=True)
#     #
#     #         return arrivals_list_final_df, stop_name
#     #
#     #     except:
#     #         arrivals_list_final_df=\
#     #             pd.DataFrame(\
#     #                 columns=['pkey','pt','rd','stop_id','stop_name','v','timestamp','delta'],\
#     #                 data=[['0000000', '3', self.route, self.stop,'N/A', 'N/A', datetime.time(0,1), datetime.timedelta(seconds=0)]])
#     #         stop_name = 'N/A'
#     #         self.arrivals_table_time_created = datetime.datetime.now()
#     #         return arrivals_list_final_df, stop_name
#
#
#     def get_hourly_frequency(self,route, stop, period):
#         results = pd.DataFrame()
#         self.arrivals_list_final_df['delta_int'] = self.arrivals_list_final_df['delta'].dt.seconds
#
#         try:
#
#             # results['frequency']= (self.arrivals_list_final_df.delta_int.resample('H').mean())//60
#             results = (self.arrivals_list_final_df.groupby(self.arrivals_list_final_df.index.hour).mean())//60
#             results = results.rename(columns={'delta_int': 'frequency'})
#             results = results.drop(['pkey'], axis=1)
#             results['hour'] = results.index
#
#         except TypeError:
#             pass
#
#         except AttributeError:
#             results = pd.DataFrame()
#
#         return results
