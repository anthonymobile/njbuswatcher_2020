import pandas as pd
import StopsDB,BusRouteLogsDB

def timestamp_fix(data): # trim the microseconds off the timestamp and convert it to datetime format
    data['timestamp'] = data['timestamp'].str.split('.').str.get(0)
    data = data.set_index(pd.DatetimeIndex(data['timestamp']), drop=False)
    return data


class StopReport: #---------------------------------------------
    # creates a object with properties that contain all the content that will be
    # rendered by the template - e.g. lists that will get iterated over into tables for display

    def __init__(self,route,stop):
        self.route=route
        self.stop=stop
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
            dict_ins['v'] = row['v']
            dict_ins['timestamp'] = row['timestamp']
            self.approach_results.append(dict_ins)
        return


    def get_arrivals1(self, period): # method 1: last approach in a contiguous sequence with 'approaching'

        self.period = period
        if period == "daily":
            arrival_query = ('SELECT * FROM %s WHERE (stop_id= %s AND pt = "APPROACHING" AND (DATE(`timestamp`) = CURDATE()) ORDER BY stop_id,timestamp;' % (self.table_name,self.stop))

        elif period=="weekly":
            arrival_query = ('SELECT * FROM %s WHERE (stop_id= %s AND pt = "APPROACHING" AND (YEARWEEK(`timestamp`, 1) = YEARWEEK(CURDATE(), 1))) ORDER BY stop_id,timestamp;' % (self.table_name,self.stop))

        elif period=="history":
            arrival_query = ('SELECT * FROM %s WHERE (stop_id= %s AND pt = "APPROACHING") ORDER BY stop_id,timestamp;' % (self.table_name,self.stop))

        df = pd.read_sql_query(arrival_query, self.conn)
        df = timestamp_fix(df)

        #
        # process the df to only take the last one from each 'approaching' sequence
        #
        #     for s in stoplist:
        #         df_stop = df.loc[df.stop_id == s]
        #
        #         df_stop['delta'] = df_stop['timestamp'] - df_stop['timestamp'].shift(1)
        #
        #
        #         for index, row in df_stop.iterrows():
        #             dict_ins = {}
        #             dict_ins['stop_id'] = row['stop_id']
        #             dict_ins['v'] = row['v']
        #             dict_ins['timestamp'] = row['timestamp']
        #             try:
        #                 dict_ins['delta'] = row['delta'].seconds
        #             except:
        #                 dict_ins['delta'] = row['delta']
        #             arrivals_history_full.append(dict_ins)
        #

        # return final list of arrivals
        self.arrivals = []
        for index, row in df.iterrows():
            dict_ins = {}
            # dict_ins['stop_id'] = row['stop_id']
            # dict_ins['v'] = row['v']
            # dict_ins['timestamp'] = row['timestamp']
            self.arrivals.append(dict_ins)
        return


    def get_arrivals2(self, period):
        # method 2: geolocated bus to stop using route log tables
        # (e.g. routelog_87) and stop lat/lon from Route.Stop class

        self.db_routelog = BusRouteLogsDB.MySQL('buses', 'buswatcher', 'njtransit', '127.0.0.1', self.route)

        return

