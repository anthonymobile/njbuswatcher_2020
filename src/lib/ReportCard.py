import pandas as pd
import StopsDB, BusAPI
import datetime

def timestamp_fix(data): # trim the microseconds off the timestamp and convert it to datetime format

    data['timestamp'] = data['timestamp'].str.split('.').str.get(0)
    data['timestamp'] = pd.to_datetime(data['timestamp'],errors='coerce')
    data = data.set_index(pd.DatetimeIndex(data['timestamp']))

    # data = data.set_index(pd.DatetimeIndex(data['timestamp'], drop=False)

    return data


def get_stoplist(source,route):

    stops_points_inbound = []
    stops_points_outbound = []

    route = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data(source, 'routes',route=route))

    stops_points_inbound_outbound = route

    # for j in route[0].paths[0]:
    #    for k in points[j]:
    #         if isinstance(k, Buses.Route.Stop):
    #             stops_points_inbound.append(k)
    #
    # for j in route[0].paths[1]:
    #    for k in points[j]:
    #        if isinstance(k, Buses.Route.Stop):
    #            stops_points_outbound.append(k)
    #
    # stops_points_inbound_outbound = [stops_points_inbound,stops_points_outbound]

    return stops_points_inbound_outbound



class StopReport: #---------------------------------------------
    # creates a object with properties that contain all the content that will be
    # rendered by the template - e.g. lists that will get iterated over into tables for display

    def __init__(self,route,stop):
        self.route=route
        self.stop=stop
        #todo self.stop_name = tk
        self.db = StopsDB.MySQL('buses', 'buswatcher', 'njtransit', '127.0.0.1', self.route)
        self.conn = self.db.conn
        self.table_name = 'stop_approaches_log_' + self.route

    def get_approaches(self,period):
        self.period = period
        if period == "daily":
            approach_query = ('SELECT * FROM %s WHERE (stop_id= %s AND (DATE(`timestamp`) = CURDATE()) ORDER BY stop_id,timestamp;' % (self.table_name,self.stop))

        elif period=="weekly":
            approach_query = ('SELECT * FROM %s WHERE (stop_id= %s AND (YEARWEEK(`timestamp`, 1) = YEARWEEK(CURDATE(), 1))) ORDER BY stop_id,timestamp;' % (self.table_name,self.stop))

        elif period=="history":
            approach_query = ('SELECT * FROM %s WHERE stop_id= %s ORDER BY stop_id,timestamp;' % (self.table_name,self.stop))

        df = pd.read_sql_query(approach_query, self.conn)
        df = timestamp_fix(df)

        # return raw list of approaches
        self.approach_results = []
        for index, row in df.iterrows():
            dict_ins = {}
            dict_ins['stop_id'] = row['stop_id']
            # dict_ins['stop_name'] = row['stop_name']
            dict_ins['v'] = row['v']
            dict_ins['pt'] = row['pt']
            dict_ins['timestamp'] = row['timestamp']
            self.approach_results.append(dict_ins)
        return


    def get_arrivals(self, period): # method 1: last approach in a contiguous sequence with 'approaching'

        self.arrivals_table_generated = None
        self.period = period
        if period == "daily":
            final_approach_query = ('SELECT * FROM %s WHERE (stop_id= %s AND pt = "APPROACHING" AND DATE(`timestamp`)=CURDATE() ) ORDER BY timestamp;' % (self.table_name, self.stop))

        elif period=="weekly":
            final_approach_query = ('SELECT * FROM %s WHERE (stop_id= %s AND pt = "APPROACHING" AND (YEARWEEK(`timestamp`, 1) = YEARWEEK(CURDATE(), 1))) ORDER BY timestamp;' % (self.table_name,self.stop))

        elif period=="history":
            final_approach_query = ('SELECT * FROM %s WHERE (stop_id= %s AND pt = "APPROACHING") ORDER BY timestamp;' % (self.table_name,self.stop))

        # get data and basic cleanup
        df_temp = pd.read_sql_query(final_approach_query, self.conn)
        df_temp = df_temp.drop(columns=['cars', 'consist', 'fd', 'm', 'name', 'rn', 'scheduled'])
        df_temp = timestamp_fix(df_temp)

        # split final approach history (sorted by timestamp) at each change in vehicle_id
        # per https://stackoverflow.com/questions/41144231/python-how-to-split-pandas-dataframe-into-subsets-based-on-the-value-in-the-fir
        #outputs a list of dfs

        final_approach_dfs = [g for i, g in df_temp.groupby(df_temp['v'].ne(df_temp['v'].shift()).cumsum())]

        # take the last V in each df and  add it to final list of arrivals
        self.arrivals_list_final_df = pd.DataFrame()
        for final_approach in final_approach_dfs:  # iterate over every final approach
            arrival_insert_df = final_approach.tail(1)  # take the last observation
            self.arrivals_list_final_df = self.arrivals_list_final_df.append(arrival_insert_df)  # insert into df

        # log the time arrivals table was generated
        self.arrivals_table_generated = datetime.datetime.now()

        return


    def delta_list(self): # create a list of tuples [arrivaltime, time since last bus]

        ## FROM OLD CODE
        ## compute interval between this bus and next in log (WORKING)
        #df_stop['delta'] = df_stop['timestamp'] - df_stop['timestamp'].shift(1)
        print (self.arrivals_list_final_df.iloc[2]['timestamp'])
        print type(self.arrivals_list_final_df.iloc[2]['timestamp'])

        self.arrivals_list_final_df['delta']=datetime.datetime.now()
        # print self.arrivals_list_final_df['timestamp'],type(self.arrivals_list_final_df['timestamp'])
        # print self.arrivals_list_final_df['timestamp'].shift(1),type(self.arrivals_list_final_df['timestamp'].shift(1))
        self.arrivals_list_final_df['delta']=self.arrivals_list_final_df['timestamp'] - self.arrivals_list_final_df['timestamp'].shift()

        return


