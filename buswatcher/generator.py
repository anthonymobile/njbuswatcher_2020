# generator.py
#
# description:
# does hourly, daily RouteReport,StopReport generation to db or json so they don't run on page loads
#
# usage:
# (statewide)                                           generator.py --statewide
# (only routes in defined collections)                  generator.py
#
#
import argparse

from buswatcher.lib.DataBases import SQLAlchemyDBConnection, Trip, BusPosition, ScheduledStop
from buswatcher.lib.RouteConfig import load_config
from buswatcher.lib.CommonTools import timeit

# todo 0 refactor all the CPU-intensive tasks for wwwAPI.RouteReport and StopReport in here

def generate_bunching_report(RouteReport):

    # TO DO THIS OUTPUTS TO a table of JSON in the db

    #
    # check if bunching leaderboard is current
    #
    #     # if no - create it
    #     # if yes load it
    #
    #
    # with SQLAlchemyDBConnection() as db:
    #     # generates top 10 list of stops on the route by # of bunching incidents for period
    #     bunching_leaderboard = []
    #     cum_arrival_total = 0
    #     cum_bunch_total = 0
    #     for service in self.route_stop_list:
    #
    #
    #         for stop in service.stops: # first query to make sure there are ScheduledStop instances
    #             bunch_total = 0
    #             arrival_total = 0
    #             report = StopReport(self.source, self.route, stop.identity, period)
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
    #     # # compute grade
    #     # # based on pct of all stops on route during period that were bunched
    #     # try:
    #     #     grade_numeric = (cum_bunch_total / cum_arrival_total) * 100
    #     #     for g in self.grade_descriptions:
    #     #         if g['bounds'][0] < grade_numeric <= g['bounds'][1]:
    #     #             self.grade = g['grade']
    #     #             self.grade_description = g['description']
    #     # except:
    #     #     self.grade = 'N/A'
    #     #     self.grade_description = 'Unable to determine grade.'
    #     #     pass
    #     #
    #     # time_created = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    #     # bunching_leaderboard_pickle = dict(bunching_leaderboard=bunching_leaderboard, grade=self.grade,
    #     #                                    grade_numeric=grade_numeric, grade_description=self.grade_description, time_created=time_created)
    #     # outfile = ('data/bunching_leaderboard_'+route+'.pickle')
    #     # with open(outfile, 'wb') as handle:
    #     #     pickle.dump(bunching_leaderboard_pickle, handle, protocol=pickle.HIGHEST_PROTOCOL)
    #
    #     # def load_bunching_leaderboard(self,route):
    #     #         infile = ('data/bunching_leaderboard_'+route+'.pickle')
    #     #         with open(infile, 'rb') as handle:
    #     #             b = pickle.load(handle)
    #     #         return b['bunching_leaderboard'], b['grade'], b['grade_numeric'], b['grade_description'], b['time_created']


#
# class RouteScan:
#
#     # @timeit
#     def __init__(self, route, statewide,system_map_xml):
#
#         # apply passed parameters to instance
#         self.route = route
#         self.statewide = statewide
#         self.system_map_xml = system_map_xml
#         self.route_map_xml = self.filter_system_map_xml()
#
#         # create database connectio
#         self.db = SQLAlchemyDBConnection()
#
#         # initialize instance variables
#         self.buses = []
#         self.trip_list = []
#
#         #  populate route basics from config
#         self.route_definitions, self.grade_descriptions, self.collection_descriptions = load_config()
#
#         # generate scan data and results
#         with SQLAlchemyDBConnection() as self.db:
#             self.fetch_positions()
#             self.parse_positions()
#             self.localize_positions()
#             self.interpolate_missed_stops()
#             self.assign_positions()
#
#     def filter_system_map_xml(self):
#         for route in self.system_map_xml.route_geometries:
#             if route['route'] == self.route:
#                 return route
#             else:
#                 continue
#
# def f_timing(self, stop_df):
#     stop_df['delta'] = (stop_df['arrival_timestamp'] - stop_df['arrival_timestamp'].shift(1)).fillna(
#         0)  # calc interval between last bus for each row, fill NaNs
#     stop_df = stop_df.dropna()  # drop the NaN (probably just the first one)
#     return stop_df
#
#
# def get_headway(
#         self):
#     with SQLAlchemyDBConnection() as db:
#
#         # build the query
#         x, trips_on_road_now = self.__get_current_trips()
#
#         query = db.session.query(ScheduledStop). \
#             add_columns(ScheduledStop.trip_id,
#                         ScheduledStop.stop_id,
#                         ScheduledStop.stop_name,
#                         ScheduledStop.arrival_timestamp)
#
#         # example of multi-table query -- would it require re-setting the relationships in DataBases.py class definitions?
#         # # query = df.session.query(Trip, ScheduledStop, BusPosition).join(ScheduledStop).join(BusPosition)
#
#         # add the period
#         query = self.__query_factory(db, query,
#                                      period=self.period)
#         # # add extra filters -- EXCLUDES current trips
#         # query=query\
#         #     .filter(ScheduledStop.trip_id.notin_(trips_on_road_now))\
#         #     .order_by(ScheduledStop.trip_id.asc())\
#         #     .order_by(ScheduledStop.pkey.asc())\
#         #     .statement
#
#         # add extra filters -- INCLUDES current trips
#         query = query \
#             .order_by(ScheduledStop.trip_id.asc()) \
#             .order_by(ScheduledStop.pkey.asc()) \
#             .statement
#
#         # execute query + if the database didn't have results, return an dummy dataframe
#         arrivals_in_completed_trips = pd.read_sql(query, db.session.bind)
#         if len(arrivals_in_completed_trips.index) == 0:
#             arrivals_in_completed_trips = pd.DataFrame(
#                 columns=['trip_id', 'stop_id', 'stop_name', 'arrival_timestamp'],
#                 data=[['666_666_20100101', '38000', 'Dummy Stop', datetime.datetime(2010, 1, 1, 7, 0, 0)],
#                       ['123_666_20100101', '38000', 'Dummy Stop', datetime.datetime(2010, 1, 1, 7, 10, 0)],
#                       ['666_666_20100101', '38001', 'Dummy Stop', datetime.datetime(2010, 1, 1, 7, 10, 0)],
#                       ['123_666_20100101', '38001', 'Dummy Stop', datetime.datetime(2010, 1, 1, 7, 21, 0)],
#                       ['666_666_20100101', '38002', 'Dummy Stop', datetime.datetime(2010, 1, 1, 7, 20, 0)],
#                       ['123_666_20100101', '38002', 'Dummy Stop', datetime.datetime(2010, 1, 1, 7, 28, 0)]]
#             )
#
#         # split by stop_id and calculate arrival intervals at each stop
#         stop_dfs = [g for i, g in arrivals_in_completed_trips.groupby(
#             arrivals_in_completed_trips['stop_id'].ne(arrivals_in_completed_trips['stop_id'].shift()).cumsum())]
#         headways_df = pd.DataFrame()
#
#         for stop_df in stop_dfs:  # iterate over every stop
#             headways_df = headways_df.append(self.f_timing(stop_df))  # dump all these rows into the headways list
#
#         # assemble the results and return
#         headway = dict()
#         # average headway for route -- entire period
#         headway['period_mean'] = headways_df['delta'].mean()
#         headway['period_std'] = headways_df['delta'].std()
#
#         # average headway for route -- by hour
#         times = pd.DatetimeIndex(headways_df.arrival_timestamp)
#         # hourly_arrival_groups = headways_df.groupby([times.hour, times.minute])
#         hourly_arrival_groups = headways_df.groupby([times.hour])
#         headway['hourly_table'] = list()
#
#         for hourly_arrivals in hourly_arrival_groups:
#             df_hourly_arrivals = hourly_arrivals[1]  # grab the df from the tuple
#             hour = datetime.time(7)
#
#             # try this https://stackoverflow.com/questions/45239742/aggregations-for-timedelta-values-in-the-python-dataframe
#             mean = df_hourly_arrivals.delta.mean(numeric_only=False)
#             std = df_hourly_arrivals.delta.std(numeric_only=False)
#
#             # compute the summary stats using numpy per https://stackoverflow.com/questions/44616546/finding-the-mean-and-standard-deviation-of-a-timedelta-object-in-pandas-df
#             # mean2 = df_hourly_arrivals.delta.apply(lambda x: np.mean(x))
#             # std2 = df_hourly_arrivals.delta.apply(lambda x: np.std(x))
#
#             headway['hourly_table'].append((hour, mean, std))
#
#         # to do average headway -- by hour, by stop
#
#         return headway
#
#
# def get_traveltime(self, period):
#
#     with SQLAlchemyDBConnection() as db:
#         traveltime = dict()
#
#         # # get a list of all COMPLETED trips on this route for this period
#         #
#         # todays_date = datetime.date.today()
#         # yesterdays_date = datetime.date.today() - datetime.timedelta(1)
#         # one_hour_ago = datetime.datetime.now() - datetime.timedelta(hours=1)
#         #
#         # x, trips_on_road_now = self.__get_current_trips()
#         #
#         #
#         # if self.period == 'now':
#         #     arrivals_in_completed_trips = pd.read_sql(
#         #         db.session.query(ScheduledStop.trip_id,
#         #                          ScheduledStop.stop_id,
#         #                          ScheduledStop.stop_name,
#         #                          ScheduledStop.arrival_timestamp)
#         #             .filter(ScheduledStop.arrival_timestamp != None)
#         #             # to dolast hour doesnt work
#         #             .filter(func.date(ScheduledStop.arrival_timestamp) > one_hour_ago)
#         #             .filter(ScheduledStop.trip_id.notin_(trips_on_road_now))
#         #             .order_by(ScheduledStop.trip_id.asc())
#         #             .order_by(ScheduledStop.arrival_timestamp.asc())
#         #             .statement,
#         #         db.session.bind)
#         #
#         # elif self.period == 'today':
#         #     arrivals_in_completed_trips = pd.read_sql(
#         #         db.session.query(ScheduledStop.trip_id,
#         #                          ScheduledStop.stop_id,
#         #                          ScheduledStop.stop_name,
#         #                          ScheduledStop.arrival_timestamp)
#         #             .filter(ScheduledStop.arrival_timestamp != None)
#         #             .filter(func.date(ScheduledStop.arrival_timestamp) == todays_date)
#         #             .filter(ScheduledStop.trip_id.notin_(trips_on_road_now))
#         #             .order_by(ScheduledStop.trip_id.asc())
#         #             .order_by(ScheduledStop.arrival_timestamp.asc())
#         #             .statement,
#         #         db.session.bind)
#         #
#         #
#         # elif self.period == 'yesterday':
#         #     arrivals_in_completed_trips = pd.read_sql(
#         #         db.session.query(ScheduledStop.trip_id,
#         #                          ScheduledStop.stop_id,
#         #                          ScheduledStop.stop_name,
#         #                          ScheduledStop.arrival_timestamp)
#         #             .filter(ScheduledStop.arrival_timestamp != None)
#         #             .filter(func.date(ScheduledStop.arrival_timestamp) == yesterdays_date)
#         #             .filter(ScheduledStop.trip_id.notin_(trips_on_road_now))
#         #             .order_by(ScheduledStop.trip_id.asc())
#         #             .order_by(ScheduledStop.arrival_timestamp.asc())
#         #             .statement,
#         #         db.session.bind)
#         #
#         # elif self.period == 'history':
#         #     arrivals_in_completed_trips = pd.read_sql(
#         #         db.session.query(ScheduledStop.trip_id,
#         #                          ScheduledStop.stop_id,
#         #                          ScheduledStop.stop_name,
#         #                          ScheduledStop.arrival_timestamp)
#         #             .filter(ScheduledStop.arrival_timestamp != None)
#         #             .filter(ScheduledStop.trip_id.notin_(trips_on_road_now))
#         #             .order_by(ScheduledStop.trip_id.asc())
#         #             .order_by(ScheduledStop.arrival_timestamp.asc())
#         #             .statement,
#         #         db.session.bind)
#         #
#         #
#         # # now, using pandas, find the difference in arrival_timestamp between first and last row of each group
#         #
#         # # Group the data frame by month and item and extract a number of stats from each group
#         #
#         # trip_start_end_times = arrivals_in_completed_trips.groupby("trip_id").agg({"arrival_timestamp": "min", "arrival_timestamp": "max"})
#         #
#         # travel_times = []
#         # # now calculate the duration of the min:max tuples in trip_start_end_times, then average of those
#         # for min,max in trip_start_end_times:
#         #     travel_times.append(str(max-min))
#         # traveltime['time'] = '%.0f' % (sum(travel_times) / float(len(travel_times))
#
#         traveltime['time'] = 20
#
#         return traveltime


#     def function_called_by_init(self):
#
#         return

#     def class_method(self):
#
#         return

def fetch_bunching_report(RouteReport):


@timeit # only need to isolate this in a function so we can timeit
def main_loop():

    if args.statewide is False:
        print ('do something')
    elif args.statewide is True:
        print ('do something')
    return

if __name__ == "__main__":


    route_definitions, grade_descriptions, collection_descriptions = load_config()
    route_definitions = route_definitions['route_definitions'] # ignore the ttl, last_updated key:value pairs

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--statewide', dest='statewide', action='store_true', help='Watch all active routes in NJ. (requires lots of CPU).')
    args = parser.parse_args()

    if args.statewide is False:
        print('running in collections mode (watch all routes in all collections)')
    elif args.statewide is True:
        print('running in statewide mode (watch all routes in NJ)')

    run_frequency = 3600 # seconds, runs once per hour
    time_start=time.monotonic()

    while True:
        main_loop()
        print('***sleeping***')
        time.sleep(run_frequency - ((time.monotonic() - time_start) % run_frequency))  # sleep remainder of the 60 second loop




