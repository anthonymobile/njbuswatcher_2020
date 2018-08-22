import pandas as pd
import StopsDB, BusAPI
import datetime
import gmaps
import config


class RouteReport:

    def __init__(self, source, route, reportcard_routes):

        # apply passed parameters to instance
        self.source = source
        self.route = route
        self.reportcard_routes = reportcard_routes

        # database initialization
        self.db = StopsDB.MySQL('buses', 'buswatcher', 'njtransit', '127.0.0.1', self.route)
        self.conn = self.db.conn
        self.table_name = 'stop_approaches_log_' + self.route

        # populate report card data
        self.get_routename()
        self.compute_grade()
        self.get_stoplist()

    def get_routename(self):

        routedata = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data(self.source, 'routes', route=self.route))
        self.routename=routedata[0].nm
        return

    def compute_grade(self):

        # for now, grade is coded manually in route_config.py
        for route in self.reportcard_routes:

            if route['route'] == self.route:
                self.grade = route['grade']
            else:
                pass
        # todo fancier grade calculation based on historical data
        return

    def get_stoplist(self): # todo rework this big time - may be looping improperly (why it repeats 2x for 2 services, 3x for 3 etc.)

        routedata = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data(self.source, 'routes', route=self.route))

        route_list = []
        for i in routedata:
            path_list = []
            for path in i.paths:
                stops_points = []
                for point in path.points:
                    if isinstance(point, BusAPI.Route.Stop):
                        stops_points.append(point)

                path_list.append(stops_points)

            route_list.append(path_list)

        self.route_stop_list = route_list[0]  # keep only a single copy of the services list


class StopReport:

    def __init__(self,route,stop):

        # apply passed parameters to instance
        self.route=route
        self.stop=stop

        # database initialization
        self.db = StopsDB.MySQL('buses', 'buswatcher', 'njtransit', '127.0.0.1', self.route)
        self.conn = self.db.conn
        self.table_name = 'stop_approaches_log_' + self.route

        # populate stop report data
        self.get_arrivals(period='daily')

    def get_arrivals(self, period):
        # method 1: last approach in a contiguous sequence with 'approaching'

        self.arrivals_table_generated = None
        self.period = period
        if period == "daily":
            final_approach_query = ('SELECT * FROM %s WHERE (stop_id= %s AND pt = "APPROACHING" AND DATE(`timestamp`)=CURDATE() ) ORDER BY timestamp DESC;' % (self.table_name, self.stop))

        elif period=="weekly":
            final_approach_query = ('SELECT * FROM %s WHERE (stop_id= %s AND pt = "APPROACHING" AND (YEARWEEK(`timestamp`, 1) = YEARWEEK(CURDATE(), 1))) ORDER BY timestamp DESC;' % (self.table_name,self.stop))

        elif period=="history":
            final_approach_query = ('SELECT * FROM %s WHERE (stop_id= %s AND pt = "APPROACHING") ORDER BY timestamp DESC;' % (self.table_name,self.stop))
        else:
            raise RuntimeError('Bad request sucker!')


        # get data and basic cleanup
        df_temp = pd.read_sql_query(final_approach_query, self.conn)
        df_temp = df_temp.drop(columns=['cars', 'consist', 'fd', 'm', 'name', 'rn', 'scheduled'])
        df_temp = timestamp_fix(df_temp)

        # split final approach history (sorted by timestamp) at each change in vehicle_id
        # per https://stackoverflow.com/questions/41144231/python-how-to-split-pandas-dataframe-into-subsets-based-on-the-value-in-the-fir
        #outputs a list of dfs

        final_approach_dfs = [g for i, g in df_temp.groupby(df_temp['v'].ne(df_temp['v'].shift()).cumsum())]

        # take the last V in each df and add it to final list of arrivals
        self.arrivals_list_final_df = pd.DataFrame()
        for final_approach in final_approach_dfs:  # iterate over every final approach
            arrival_insert_df = final_approach.tail(1)  # take the last observation
            self.arrivals_list_final_df = self.arrivals_list_final_df.append(arrival_insert_df)  # insert into df

        # log the time arrivals table was generated
        self.arrivals_table_generated = datetime.datetime.now()

        # loop and calc delta for each row, fill NaNs
        for index,row in self.arrivals_list_final_df.iterrows():
            # row['delta']=row['timestamp']-row['timestamp'].shift()
            row['delta']='0 min'
        # self.arrivals_list_final_df['delta'].fillna(0)

        return


    def route_map(self):

        gmaps.configure(api_key=config.free_maps_api_key)

        bus_reports = BusAPI.parse_xml_getBusesForRouteAll(BusAPI.get_xml_data('nj', 'all_buses'))

        bus_points = []
        for bus in bus_reports:
            if bus.rt == self.route:
                bus_points.append(bus)

        self.m = gmaps.Map()
        self.m.add_layer(gmaps.symbol_layer([(float(b.lat), float(b.lon)) for b in bus_points], fill_color='green', stroke_color='green', scale=2))
        return



def timestamp_fix(data): # trim the microseconds off the timestamp and convert it to datetime format

    data['timestamp'] = data['timestamp'].str.split('.').str.get(0)
    data['timestamp'] = pd.to_datetime(data['timestamp'],errors='coerce')
    data = data.set_index(pd.DatetimeIndex(data['timestamp']))

    # data = data.set_index(pd.DatetimeIndex(data['timestamp'], drop=False)

    return data

