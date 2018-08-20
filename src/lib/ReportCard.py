import pandas as pd
import StopsDB, BusAPI
import datetime
import gmaps
import config

def timestamp_fix(data): # trim the microseconds off the timestamp and convert it to datetime format

    data['timestamp'] = data['timestamp'].str.split('.').str.get(0)
    data['timestamp'] = pd.to_datetime(data['timestamp'],errors='coerce')
    data = data.set_index(pd.DatetimeIndex(data['timestamp']))

    # data = data.set_index(pd.DatetimeIndex(data['timestamp'], drop=False)

    return data


def get_stoplist(source,route):

    routedata = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data(source, 'routes',route=route))

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

    route_stop_list = route_list[0] # chop off the duplicate half
    # route_stop_list = route_list

    return route_stop_list # list with 2 lists of stops for inbound and outbound

class StopReport: #---------------------------------------------

    def __init__(self,route,stop):
        self.route=route
        self.stop=stop
        self.db = StopsDB.MySQL('buses', 'buswatcher', 'njtransit', '127.0.0.1', self.route)
        self.conn = self.db.conn
        self.table_name = 'stop_approaches_log_' + self.route

    def get_arrivals(self, period): # method 1: last approach in a contiguous sequence with 'approaching'

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

    # def get_approaches(self,period):
    #     self.period = period
    #     if period == "daily":
    #         approach_query = ('SELECT * FROM %s WHERE (stop_id= %s AND (DATE(`timestamp`) = CURDATE()) ORDER BY stop_id,timestamp;' % (self.table_name,self.stop))
    #
    #     elif period=="weekly":
    #         approach_query = ('SELECT * FROM %s WHERE (stop_id= %s AND (YEARWEEK(`timestamp`, 1) = YEARWEEK(CURDATE(), 1))) ORDER BY stop_id,timestamp;' % (self.table_name,self.stop))
    #
    #     elif period=="history":
    #         approach_query = ('SELECT * FROM %s WHERE stop_id= %s ORDER BY stop_id,timestamp;' % (self.table_name,self.stop))
    #
    #     df = pd.read_sql_query(approach_query, self.conn)
    #     df = timestamp_fix(df)
    #
    #     # return raw list of approaches
    #     self.approach_results = []
    #     for index, row in df.iterrows():
    #         dict_ins = {}
    #         dict_ins['stop_id'] = row['stop_id']
    #         # dict_ins['stop_name'] = row['stop_name']
    #         dict_ins['v'] = row['v']
    #         dict_ins['pt'] = row['pt']
    #         dict_ins['timestamp'] = row['timestamp']
    #         self.approach_results.append(dict_ins)
    #     return


class RouteGrade:

    def __init__(self, route):
        self.route = route
        self.db = StopsDB.MySQL('buses', 'buswatcher', 'njtransit', '127.0.0.1', self.route)
        self.conn = self.db.conn
        self.table_name = 'stop_approaches_log_' + self.route

    def compute_grade(self):
        self.grade = 'B-'
        return

