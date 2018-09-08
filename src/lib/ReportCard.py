import datetime, time, sys
from operator import itemgetter
import pandas as pd

# import app libraries
import StopsDB, BusAPI

# setup cache
from easy_cache import ecached
from functools import partial
memcached = partial(ecached, cache_alias='memcached')

# common functions
def timestamp_fix(data): # trim the microseconds off the timestamp and convert it to datetime format
    data['timestamp'] = data['timestamp'].str.split('.').str.get(0)
    data['timestamp'] = pd.to_datetime(data['timestamp'],errors='coerce')
    data = data.set_index(pd.DatetimeIndex(data['timestamp']))
    # data = data.set_index(pd.DatetimeIndex(data['timestamp'], drop=False)
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

    def __init__(self, source, route, reportcard_routes, grade_descriptions):

        # apply passed parameters to instance
        self.source = source
        self.route = route
        self.reportcard_routes = reportcard_routes
        self.grade_descriptions = grade_descriptions

        # database initialization
        self.db = StopsDB.MySQL('buses', 'buswatcher', 'njtransit', '127.0.0.1', self.route)
        self.conn = self.db.conn
        self.table_name = 'stop_approaches_log_' + self.route

        # populate report card data
        self.get_routename()
        self.get_servicelist()
        self.compute_grade()
        self.get_stoplist()
        self.bunching_leaderboard = self.get_bunching_leaderboard('daily',self.route)

    def get_routename(self):
        routedata = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data(self.source, 'routes', route=self.route))
        self.routename=routedata[0].nm
        return

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


    def get_stoplist(self):

        routedata = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data(self.source, 'routes', route=self.route))
        route_stop_list_temp = []
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
            route_stop_list_temp.append(path_list)
        self.route_stop_list = route_stop_list_temp[0] # transpose a single copy since the others are all repeats (can be verified by path ids)
        return

    @memcached('get_bunching_leaderboard', timeout=600) # change this for dynamic cache name based on route number
    def get_bunching_leaderboard(self, period,route):
        # generates top 10 list of stops on the route by # of bunching incidents for yesterday
        # as well as the hourly frequency table

        # sample query
        # SELECT * FROM stop_approaches_log_87 WHERE (stop_id= 20935 AND DATE(timestamp)=CURDATE()) ORDER BY timestamp DESC;

        bunching_leaderboard = []

        # loop over each service and stop
        for service in self.route_stop_list:
            # print service.id
            for stop in service.stops:
                bunch_total = 0
                report = StopReport(self.route, stop.identity,period)
                # calculate number of bunches
                for (index, row) in report.arrivals_list_final_df.iterrows():
                    if (row.delta > report.bigbang) and (row.delta <= report.bunching_interval):
                        # print "\t",row.v,"\t",stop.st,"\t\t\t\t\t",row.timestamp,"\t",row.delta
                        bunch_total += 1
                        # sys.stdout.write('.'),

                # append dict to the list
                bunching_leaderboard.append((stop.st, bunch_total,stop.identity))

                # now work on the hourly frequency report

        # sort stops by number of bunchings, grab first 10
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
        self.db = StopsDB.MySQL('buses', 'buswatcher', 'njtransit', '127.0.0.1', self.route)
        self.conn = self.db.conn
        self.table_name = 'stop_approaches_log_' + self.route
        # populate stop report data
        self.get_arrivals()


    def get_arrivals(self):
        self.arrivals_table_time_created = None

        if self.period == "daily":
            final_approach_query = ('SELECT * FROM %s WHERE (stop_id= %s AND DATE(`timestamp`)=CURDATE() ) ORDER BY timestamp DESC;' % (self.table_name, self.stop))
        elif self.period == "yesterday": # todo 'yesterday' query returns empty set
            final_approach_query = ('SELECT * FROM %s WHERE (stop_id= %s AND DATE(timestamp >= DATE_SUB(CURDATE(), INTERVAL 1 DAY) AND timestamp < CURDATE()) ) ORDER BY timestamp DESC;' % (self.table_name, self.stop))
        elif self.period=="weekly":
            final_approach_query = ('SELECT * FROM %s WHERE (stop_id= %s AND (YEARWEEK(`timestamp`, 1) = YEARWEEK(CURDATE(), 1))) ORDER BY timestamp DESC;' % (self.table_name,self.stop))
        elif self.period=="history":
            final_approach_query = ('SELECT * FROM %s WHERE stop_id= %s ORDER BY timestamp DESC;' % (self.table_name,self.stop))
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
            self.arrivals_list_final_df = pd.DataFrame()
            for final_approach in final_approach_dfs:  # iterate over every final approach
                arrival_insert_df = final_approach.tail(1)  # take the last observation
                self.arrivals_list_final_df = self.arrivals_list_final_df.append(arrival_insert_df)  # insert into df

            # calc interval between last bus for each row, fill NaNs
            self.arrivals_list_final_df['delta']=(self.arrivals_list_final_df['timestamp'] - self.arrivals_list_final_df['timestamp'].shift(-1)).fillna(0)

            # housekeeping ---------------------------------------------------
            # log the time arrivals table was generated
            self.arrivals_table_time_created = datetime.datetime.now()
            # set stop_name
            self.stop_name = self.arrivals_list_final_df['stop_name'].iloc[0]

        except:
            self.arrivals_list_final_df=\
                pd.DataFrame(\
                    columns=['pkey','pt','rd','stop_id','stop_name','v','timestamp','delta'],\
                    data=[['0000000', '3', self.route, self.stop,'N/A', 'N/A', datetime.time(0,1), datetime.timedelta(seconds=0)]])

        # set timedelta constant for later use in bunching analysis
        self.bunching_interval = datetime.timedelta(minutes=3)
        # set a timedelta for zero
        self.bigbang = datetime.timedelta(seconds=0)

        return


