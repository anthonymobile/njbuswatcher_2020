
        # def show_arrivals(self,period,stop):
        #     table_name = 'stop_arrival_predictions_log_' + self.route
        #
        #     arrival_query = ('SELECT * FROM %s WHERE (pt = "APPROACHING" AND stop_id= %s ) ORDER BY stop_id,timestamp;' % (table_name,stop))
        #     df = pd.read_sql_query(arrival_query, self.conn)
        #     df = timestamp_fix(df)


            # todo this is the simpler all time version
            # def render_arrivals_history_full(source, route, stoplist):
            #
            #     (conn, db) = db_setup(route)
            #
            #     arrival_query = (
            #                 'SELECT * FROM stop_predictions WHERE (rd = %s AND pt = "APPROACHING") ORDER BY stop_id,timestamp;' % route)
            #     df = pd.read_sql_query(arrival_query, conn)
            #     df = timestamp_fix(df)
            #     arrivals_history_full = []
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
            #     return arrivals_history_full


            # todo abstract below for 'period'

            #     arrivals_history = []
            #
            #     for s in stoplist:
            #
            #         df_stop = df.loc[df.stop_id == s]
            #
            #         df_stop['delta'] = df_stop['timestamp'] - df_stop['timestamp'].shift(1)
            #
            # todo resample based on period
            #         # resample hourly average
            #         # need to convert delta to numeric type first per...
            #         # https://stackoverflow.com/questions/44616546/finding-the-mean-and-standard-deviation-of-a-timedelta-object-in-pandas-df
            #
            #         df_stop['delta_int'] = df_stop['delta'].values.astype(np.int64)
            #
            #         for hour in df_stop.delta_int.resample('H').mean().iteritems():
            #             dict_ins = {}
            #             dict_ins['stop_id'] = s
            #             dict_ins['hour_top'] = hour[0]
            #             dict_ins['avg_interval'] = hour[1]
            #             arrivals_history_hourly.append(dict_ins)
            #
            #     return arrivals_history_hourly
            #
            #
    #
    #
    #
    # class RouteReport: #---------------------------------------------
    #     def __init__(self, route):
    #         self.db = BusRouteLogsDB.MySQL('buses', 'buswatcher', 'njtransit', '127.0.0.1', self.route)
    #         self.conn = self.db.conn
    #         self.stops = []
    #
    #
    #     # todo this should really just be a loop over stops
    #     # todo or better - get the list of stops from the BusAPI.Route class
    #
    #     def get_stoplist:  # get list of all stops for 'route' currently observed in the entire database
    #         stoplist_query = (
    #                 'SELECT stop_id FROM stop_predictions WHERE rd = %s GROUP BY stop_id;' % self.route)
    #         stoplist = pd.read_sql_query(stoplist_query, self.db.conn)
    #
    #         return stoplist['stop_id']
    #
    #
    #     # todo logic to handle three different <<period>> = 'history, daily, now'

        # # for a single stop, all buses seen in history
        # def render_arrivals_history_1stop(source, route, stop):
        #     # get a clean df
        #     (conn, db) = db_setup(route)
        #     arrival_query = (
        #             'SELECT * FROM stop_predictions WHERE (rd = %s AND pt = "APPROACHING" AND stop_id= %s ) ORDER BY stop_id,timestamp;' % (
        #     route, stop))
        #     df = pd.read_sql_query(arrival_query, conn)
        #     df = timestamp_fix(df)
        #
        #     # insert code derived from nb-new_stopwatcher_data_structure.ipynb
        #
        #     arrivals_history_1stop = []
        #
        #     return arrivals_history_1stop

