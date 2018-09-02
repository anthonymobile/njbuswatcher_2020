import datetime, time, sys
import pandas as pd

import StopsDB, BusAPI

# common functions
def timestamp_fix(data): # trim the microseconds off the timestamp and convert it to datetime format
    data['timestamp'] = data['timestamp'].str.split('.').str.get(0)
    data['timestamp'] = pd.to_datetime(data['timestamp'],errors='coerce')
    data = data.set_index(pd.DatetimeIndex(data['timestamp']))
    # data = data.set_index(pd.DatetimeIndex(data['timestamp'], drop=False)
    return data

def timeit(method):

    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        print '%r (%r, %r) %2.2f sec' % \
              (method.__name__, args, kw, te-ts)
        return result

    return timed

# primary classes

class RouteReport:

    class Path():
        def __init__(self):
            self.name = 'Path'
            self.stops = []
            self.id = ''
            self.d = ''
            self.dd = ''

    def __init__(self, source, route, reportcard_routes,grade_descriptions):

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
        self.compute_grade()
        self.get_stoplist()
        # self.get_bunching_leaderboard('yesterday')

    @timeit
    def get_routename(self):
        routedata = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data(self.source, 'routes', route=self.route))
        self.routename=routedata[0].nm
        return

    @timeit
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

    @timeit
    def get_stoplist(self):
        # todo BUG NJT API serves up only the routes currently running? hardcode them instead?
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

    @timeit
    def get_bunching_leaderboard(self,period):
        # generates top 10 list of stops on the route by # of bunching incidents for yesterday

        self.bunching_badboys = []

        # loop over each service and stop
        bunch_total=0
        print 'starting bunching analysis for yesterday...'
        for service in self.route_stop_list:
            for stop in service.stops:
                print stop.identity,
                report = StopReport(self.route, stop.identity,period)

                # calculate number of bunches
                for (index, row) in report.arrivals_list_final_df.iterrows():
                    if (row.delta > report.bigbang) and (row.delta <= report.bunching_interval):
                        bunch_total += 1
                        sys.stdout.write('.'),
                print
            # append tuple to the list
            self.bunching_badboys.append((stop.st, bunch_total))

        # sort stops by number of bunchings, grab first 10
        self.bunching_badboys.sort(key=bunch_total, reverse=True)
        self.bunching_badboys=self.bunching_badboys[:10]

        # todo write to a new db table for persistence
        db = StopsDB.MySQL('buses', 'buswatcher', 'njtransit', '127.0.0.1', route)
        conn = db.conn

        table_name = 'bunching_leaderboard_%s' % self.route
        create_table_string = '''CREATE TABLE IF NOT EXISTS %s (pkey integer primary key auto_increment, date varchar(20), route varchar(20), stop_id varchar(20), bunch_total varchar(20)''' % table_name

        try:
            self.conn = connection.MySQLConnection(user=self.db_user, password=self.db_password, host=self.db_host)
            self._execute('CREATE DATABASE IF NOT EXISTS %s;' % self.db_name)
            self.conn.database = self.db_name

            self._execute(create_table_string)

        except Error as err:
            print 'something went wrong with mysql'
            pass



        return

    @timeit
    def get_today_bunch_top10_v2(self):

        self.bunching_badboys = []

        # sort stops by number of bunchings, grab first 10
        self.bunching_badboys.sort(key=bunch_total, reverse=True)
        self.bunching_badboys=self.bunching_badboys[:10]
        return



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
        self.get_arrivals(self.period)

    @timeit
    def get_arrivals(self, period):
        self.arrivals_table_time_created = None
        self.period = period

        if period == "daily":
            final_approach_query = ('SELECT * FROM %s WHERE (stop_id= %s AND pt = "APPROACHING" AND DATE(`timestamp`)=CURDATE() ) ORDER BY timestamp DESC;' % (self.table_name, self.stop))

        elif period == "yesterday":
            final_approach_query = ('SELECT * FROM %s WHERE (stop_id= %s AND pt = "APPROACHING" AND DATE(timestamp >= DATE_SUB(CURDATE(), INTERVAL 1 DAY) AND timestamp < CURDATE()) ) ORDER BY timestamp DESC;' % (self.table_name, self.stop))

        elif period=="weekly":
            final_approach_query = ('SELECT * FROM %s WHERE (stop_id= %s AND pt = "APPROACHING" AND (YEARWEEK(`timestamp`, 1) = YEARWEEK(CURDATE(), 1))) ORDER BY timestamp DESC;' % (self.table_name,self.stop))
        elif period=="history":
            final_approach_query = ('SELECT * FROM %s WHERE (stop_id= %s AND pt = "APPROACHING") ORDER BY timestamp DESC;' % (self.table_name,self.stop))
        else:
            raise RuntimeError('Bad request sucker!')

        # get data and basic cleanup
        df_temp = pd.read_sql_query(final_approach_query, self.conn) # arrivals table and deltas are all re-generated on the fly for every view now -- easier, but might lead to inconsistent/innaccurate results over time?
        df_temp = df_temp.drop(columns=['cars', 'consist', 'fd', 'm', 'name', 'rn', 'scheduled'])
        df_temp = timestamp_fix(df_temp)

        # split final approach history (sorted by timestamp) at each change in vehicle_id outputs a list of dfs -- per https://stackoverflow.com/questions/41144231/python-how-to-split-pandas-dataframe-into-subsets-based-on-the-value-in-the-fir
        final_approach_dfs = [g for i, g in df_temp.groupby(df_temp['v'].ne(df_temp['v'].shift()).cumsum())]

        # todo BUG move the entire below to a try-except, and the except creates an empty self.arrivals_list_final_df ? and self.arrivals_table_time_created -- to avoind the error of no content

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


