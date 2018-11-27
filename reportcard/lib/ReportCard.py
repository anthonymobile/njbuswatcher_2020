import datetime, time, sys
from operator import itemgetter
import pandas as pd

# database config
import os
try:
    db_state = os.environ['REPORTCARD_PRODUCTION']
    db_server = '192.168.1.181'
except:
    db_server = '127.0.0.1'

# import app libraries
from . import StopsDB, BusAPI, TripsDB

# setup cache
from easy_cache import ecached
from django.conf import settings
settings.configure(DEBUG=True, DJANGO_SETTINGS_MODULE="mysite_django.settings")

def get_cache_timeout(self,route,stop,period):
    if period == "hourly":
        cache_timeout = 60 # 1 min
    elif period == "daily":
        cache_timeout = 3600  # 1 hour
    elif period == "yesterday":
        cache_timeout = 86400  # 1 day
    elif period == "weekly":
        cache_timeout = 86400  # 1 day
    elif period == "history":
        cache_timeout = 604800  # 1 week
    else:
        raise RuntimeError('Bad request sucker!')
    return cache_timeout

# def invalidate_cache(n):
#     time_consuming_operation.invalidate_cache_by_key(n)

# common functions
def timestamp_fix(data): # trim the microseconds off the timestamp and convert it to datetime format
    data['timestamp'] = data['timestamp'].str.split('.').str.get(0)
    data['timestamp'] = pd.to_datetime(data['timestamp'],errors='coerce')
    # data = data.set_index(pd.DatetimeIndex(data['timestamp']))
    data = data.set_index(pd.DatetimeIndex(data['timestamp']), drop=False)
    return data

# primary classes
class RouteReport:

    class Path():
        def __init__(self):
            self.name = 'Path'
            self.stops = []
            self.id = ''
            self.d = ''
            self.dd = ''

    def __init__(self, source, route, reportcard_routes, grade_descriptions): # replace last 2 with **kwargs to make them optional?

        # apply passed parameters to instance
        self.source = source
        self.route = route
        self.reportcard_routes = reportcard_routes
        self.grade_descriptions = grade_descriptions

        # database initialization
        self.db = StopsDB.MySQL('buses', 'buswatcher', 'njtransit', db_server, self.route)
        self.conn = self.db.conn
        self.table_name = 'stop_approaches_log_' + self.route

        # populate report card data
        self.routename, self.waypoints_coordinates, self.stops_coordinates, self.waypoints_geojson, self.stops_geojson = self.get_routename(self.route)
        self.get_servicelist()
        self.compute_grade()
        self.route_stop_list = self.get_stoplist(self.route)
        # self.bunching_leaderboard = self.get_bunching_leaderboard('daily',self.route)

    # @ecached('get_routename:{route}', timeout=86400) # cache per route, 24 hour expire
    def get_routename(self,route):
        routedata, waypoints_coordinates, stops_coordinates,waypoints_geojson, stops_geojson = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data(self.source, 'routes', route=route))
        return routedata[0].nm, waypoints_coordinates, stops_coordinates, waypoints_geojson, stops_geojson

    def get_servicelist(self):
        for route in self.reportcard_routes:
            if route['route'] == self.route:
                self.servicelist = []
                for service in route['services']:
                    insertion = {'destination':service[0],'service_id':service[1]}
                    self.servicelist.append(insertion)
                # populate servicelist with stoplist?
                # for service in self.servicelist:
                #   how to do it?
        return


    def compute_grade(self):
        # for now, grade is coded manually in route_config.py
        # FUTURE fancier grade calculation based on historical data
        for route in self.reportcard_routes:
            if route['route'] == self.route:
                self.grade = route['grade']
                self.description_long = route['description_long']
                self.prettyname = route['prettyname']
                self.schedule_url = route['schedule_url']
                self.moovit_url = route['moovit_url']
                for entry in self.grade_descriptions:
                    if self.grade == entry['grade']:
                        self.grade_description = entry['description']
                    else:
                        pass
                if not self.grade_description:
                    grade_description = 'Cannot find a description for that grade.'
                else:
                    pass
            else:
                pass
        return


    # ecached gives a pickling error on Route.Path here
    def get_stoplist(self, route):
        routedata, waypoints_coordinates, stops_coordinates, waypoints_geojson, stops_geojson = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data(self.source, 'routes', route=self.route))
        route_stop_list = []
        for r in routedata:
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

    @ecached('get_bunching_leaderboard:{route}:{period}', timeout=3600) # cache per route, period, 1 hour expire
    def get_bunching_leaderboard(self, period, route):
        # generates top 10 list of stops on the route by # of bunching incidents for period

        bunching_leaderboard = []

        for service in self.route_stop_list:
            for stop in service.stops:
                bunch_total = 0
                report = StopReport(self.route, stop.identity,period)
                for (index, row) in report.arrivals_list_final_df.iterrows():
                    if (row.delta > report.bigbang) and (row.delta <= report.bunching_interval):
                        bunch_total += 1

                bunching_leaderboard.append((stop.st, bunch_total,stop.identity))

        bunching_leaderboard.sort(key=itemgetter(1), reverse=True)
        bunching_leaderboard = bunching_leaderboard[:10]

        return bunching_leaderboard


class StopReport:

    def __init__(self,route,stop,period):

        # apply passed parameters to instance
        self.route=route
        self.stop=stop
        self.period=period

        # database initialization
        self.db = StopsDB.MySQL('buses', 'buswatcher', 'njtransit', db_server,  self.route)
        self.conn = self.db.conn
        self.table_name = 'stop_approaches_log_' + self.route

        # populate stop report data
        self.arrivals_list_final_df, self.stop_name = self.get_arrivals(self.route,self.stop,self.period)

        # constants
        self.bunching_interval = datetime.timedelta(minutes=3)
        self.bigbang = datetime.timedelta(seconds=0)


    @ecached('get_arrivals:{route}:{stop}:{period}', timeout=get_cache_timeout) # dynamic timeout
    def get_arrivals(self,route,stop,period):

        if self.period == "daily":
            final_approach_query = ('SELECT * FROM %s WHERE (rd=%s AND stop_id= %s AND DATE(`timestamp`)=CURDATE() ) ORDER BY timestamp DESC;' % (self.table_name, self.route, self.stop))
        elif self.period == "yesterday":
            final_approach_query = ('SELECT * FROM %s WHERE (rd=%s AND stop_id= %s AND (timestamp >= CURDATE() - INTERVAL 1 DAY AND timestamp < CURDATE())) ORDER BY timestamp DESC;' % (self.table_name, self.route, self.stop))
        elif self.period=="weekly":
            final_approach_query = ('SELECT * FROM %s WHERE (rd=%s AND stop_id= %s AND (YEARWEEK(`timestamp`, 1) = YEARWEEK(CURDATE(), 1))) ORDER BY timestamp DESC;' % (self.table_name, self.route, self.stop))
        elif self.period=="history":
            final_approach_query = ('SELECT * FROM %s WHERE (rd=%s AND stop_id= %s) ORDER BY timestamp DESC;' % (self.table_name, self.route, self.stop))
        else:
            raise RuntimeError('Bad request sucker!')

        # get data and basic cleanup
        df_temp = pd.read_sql_query(final_approach_query, self.conn) # arrivals table and deltas are all re-generated on the fly for every view now -- easier, but might lead to inconsistent/innaccurate results over time?
        df_temp = df_temp.drop(columns=['cars', 'consist', 'fd', 'm', 'name', 'rn', 'scheduled'])
        df_temp = timestamp_fix(df_temp)

        # split final approach history (sorted by timestamp) at each change in vehicle_id outputs a list of dfs -- per https://stackoverflow.com/questions/41144231/python-how-to-split-pandas-dataframe-into-subsets-based-on-the-value-in-the-fir
        final_approach_dfs = [g for i, g in df_temp.groupby(df_temp['v'].ne(df_temp['v'].shift()).cumsum())]

        try:
            # take the last V(ehicle) approach in each df and add it to final list of arrivals
            arrivals_list_final_df = pd.DataFrame()
            for final_approach in final_approach_dfs:  # iterate over every final approach
                arrival_insert_df = final_approach.tail(1)  # take the last observation
                arrivals_list_final_df = arrivals_list_final_df.append(arrival_insert_df)  # insert into df

            # calc interval between last bus for each row, fill NaNs
            arrivals_list_final_df['delta']=(arrivals_list_final_df['timestamp'] - arrivals_list_final_df['timestamp'].shift(-1)).fillna(0)

            # housekeeping ---------------------------------------------------

            # set stop_name
            stop_name = arrivals_list_final_df['stop_name'].iloc[0]
            return arrivals_list_final_df, stop_name

        except:
            arrivals_list_final_df=\
                pd.DataFrame(\
                    columns=['pkey','pt','rd','stop_id','stop_name','v','timestamp','delta'],\
                    data=[['0000000', '3', self.route, self.stop,'N/A', 'N/A', datetime.time(0,1), datetime.timedelta(seconds=0)]])
            stop_name = 'N/A'
            self.arrivals_table_time_created = datetime.datetime.now()
            return arrivals_list_final_df, stop_name


    @ecached('get_hourly_frequency:{route}:{stop}:{period}', timeout=get_cache_timeout)
    def get_hourly_frequency(self,route, stop, period):

        results = pd.DataFrame()
        self.arrivals_list_final_df['delta_int'] = self.arrivals_list_final_df['delta'].dt.seconds

        try:

            # results['frequency']= (self.arrivals_list_final_df.delta_int.resample('H').mean())//60
            results = (self.arrivals_list_final_df.groupby(self.arrivals_list_final_df.index.hour).mean())//60
            results = results.rename(columns={'delta_int': 'frequency'})
            results = results.drop(['pkey'], axis=1)
            results['hour'] = results.index

        except TypeError:
            pass

        except AttributeError:
            results = pd.DataFrame()

        return results

class KeyValueData:
    def __init__(self, **kwargs):
        self.name = 'KeyValueData'
        for k, v in list(kwargs.items()):
            setattr(self, k, v)

    def add_kv(self, key, value):
        setattr(self, key, value)

    def __repr__(self):
        line = []
        for prop, value in vars(self).items():
            line.append((prop, value))
        line.sort(key=lambda x: x[0])
        out_string = ' '.join([k + '=' + str(v) for k, v in line])
        return self.name + '[%s]' % out_string

    def to_dict(self):
        line = []
        for prop, value in vars(self).items():
            line.append((prop, value)) # list of tuples
        line.sort(key=lambda x: x[0])
        out_dict = dict()
        for l in line:
            out_dict[l[0]]=l[1]
        return out_dict

// TripReport is populated from the database automagically based on passed parameters
// route, run, bus id, date in 20181101 format?

class TripReport(KeyValueData):

    def __init__(self,route,run,id,date):
        KeyValueData.__init__(self)
        self.route = route
        self.name = 'triplog'
        self.trip_id = ''
        self.id = ''
        self.date = ''
        self.points = []            # points is a list of unique StopCalls and PositionReports (a PositionReport is converted to a StopCall if the inferrer decides its -the- stop call
        self.d = ''
        self.dd = ''

        # database initialization
        self.db = TripsDB.MySQL('buses', 'buswatcher', 'njtransit', db_server, self.route)
        self.conn = self.db.conn
        self.table_name = 'triplog_' + self.route

        # populate report card data (to replace StopReport in current pages)
        # self.arrivals_list_final_df, self.stop_name = self.get_arrivals(self.route, self.stop, self.period)

    # def get_arrivals:

        # ISSUE RIGHT NOW IS BELOW IS get_trips is BUILDING TRIPLOGS for every trip on the route for each stop report.
        # QUICKER DIRTY METHOD WOULD JUST

        # load the entries from the position log
        # df.readsql = query = where route = route, run = run, v = id, date (substring) = date, stop_id = stop

        # 1) for each v, assign the call time to the point of closest approach
        # 2) ignore missing buses

        # return that

        # self.arrivals_table_time_created = datetime.datetime.now()
        # return arrivals_list_final_df, stop_name

    # def get_triplogs:
        # load the entries from the position log
        # df.readsql = query = where route = route, run = run, v = id, date (substring) = date

        # iterate through all these position log entries:
            # assigning each to either an ObservedPosition object or a StopCall
                # algo for doing that is ---
                # 1) sort by stop_id,
                # 2) if there is only one entry for that stop_id for this trip, and its within a reasonable distance, log it at the call
                # 3) if there is more than one, take the one with the shortest distance
                # ISSUES TO WATCH:
                    # gaps -(e.g. stops that are missed) -- can add an interpolator loop
                    # overlaps (e.g. 87 on PAterson Plank AND PALISADE)-- can add a control loop?
                # PERFORMANCE -- cache it
            # self.points.append(it)

        # ISSUE RIGHT NOW IS BELOW IS BUILDING TRIPLOGS for every trip on the route for each stop report.
        # from these trip reports, can generate both arrivals list for this stop
        # as well as trip-specific data like "average travel time from here to end of route"


    #         self.arrivals_table_time_created = datetime.datetime.now()
    #         return arrivals_list_final_df, stop_name

    class ObservedPosition:
        def __init__(self):
            self.trip_id = ''
            self.bid = ''
            self.date = ''
            self.lat = ''
            self.lon = ''
            self.timestamp = ''

    class StopCall:
        def __init__(self):
            self.trip_id = ''
            self.bid = ''
            self.date = ''
            self.lat = ''
            self.lon = ''
            self.timestamp = ''
            self.stop_id = ''      # aka 'identity'
            self.stop_name = ''    # aka 'st'
            self.distance = ''     # aka 'bcol'

