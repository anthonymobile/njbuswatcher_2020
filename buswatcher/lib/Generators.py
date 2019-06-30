from pathlib import Path
import os
import pickle
from operator import itemgetter
import datetime
import json
from dateutil import parser
from datetime import timedelta

from .BusAPI import *
from .DataBases import SQLAlchemyDBConnection, Trip, BusPosition, ScheduledStop  # , RouteReportCache
from .wwwAPI import StopReport
from sqlalchemy import func, text


class Generator():

    def __init__(self,system_map):
        self.cwd = os.getcwd()
        self.pickle_prefix = Path(self.cwd + "config/reports/")
        self.db =  SQLAlchemyDBConnection()

    def store_pickle(self, report_to_store):
        with open(self.pickle_prefix+report_to_store['route']+'_'+report_to_store['report']['type'],"wb") as f:
            pickle.dump(report_to_store, f, protocol=pickle.HIGHEST_PROTOCOL)
        return

    def retrieve_pickle(self,route,type):
        with open(self.pickle_prefix+route+'_'+type,"rb") as f:
            report_retrieved = pickle.load(f)
        return report_retrieved

class RouteUpdater(): # todo 0 test route updater

    def __init__(self,system_map):
        self.refresh_routedata(system_map)

    def refresh_routedata(self, system_map):
        now = datetime.datetime.now()

        # even though this now runs on a daily schedule
        # load existing reports and check ttl anyways
        try:
            route_descriptions_last_updated = parser.parse(system_map.route_descriptions['last_updated'])
        except:
            route_descriptions_last_updated = parser.parse('2000-01-01 01:01:01')
        route_descriptions_ttl = timedelta(seconds=int(system_map.route_descriptions['ttl']))

        # if TTL expired, update route geometry local XMLs
        if (now - route_descriptions_last_updated) > route_descriptions_ttl:
            print ('Updating XML route definitions from remote source (NJTransit API getRoutePoints.jsp)')

            # UPDATE ROUTES FROM API

            # 1. list all routes from current definitions file and sort it by route number
            routelist = sorted([r['route'] for r in system_map.route_descriptions['routedata']])

            # 2. grab current buses list and see if there's any route #s we don't know yet
            # get list of active routes
            buses = parse_xml_getBusesForRouteAll(get_xml_data('nj', 'all_buses'))
            routes_active_tmp = [b.rt for b in buses]
            # sort by freq (not needed, but useful) and remove dupes
            routelist_sorted_unique = sorted(set(routelist), key=lambda ele: routelist.count(ele))
            # remove any bus not on a numeric route
            routes_active = list()
            for b in routelist_sorted_unique:
                try:
                    dummy = int(b)
                    routes_active.append(b)
                except:
                    continue
            routes_active.sort()
            # merge the two
            merged_routelist = routelist
            merged_routelist.extend(x for x in routes_active if x not in merged_routelist)

            # 3. create blank system_map.route_descriptions entries for any newly seen routes
            new_routes = [x for x in routes_active if x not in routelist]
            for new_route in new_routes:
                update = {"route": new_route, "nm": '', "ttl": "1d",
                          "description_long": "", "description_short": "", "frequency": "low",
                          "prettyname": "",
                          "schedule_url": "https://www.njtransit.com/sf/sf_servlet.srv?hdnPageAction=BusTo"}
                system_map.route_descriptions['routedata'].append(update)

            # 4. fetch route xml metadata from NJT API
            # the route and its nm e.g. '119 Bayonne-Jersey City-NY'
            api_response = list()
            for r in merged_routelist:
                try:
                    route_xml = parse_xml_getRoutePoints(get_xml_data('nj', 'routes', route=r))
                    route_entry = {'route': route_xml[0][0].id, 'nm': route_xml[0][0].nm}  # .id should NOT be .identity
                    api_response.append(route_entry)
                except:
                    continue

            # 5. merge API data into system_map.route_descriptions
            for a in api_response: # iterate over routes fetched from API
                for r in system_map.route_descriptions['routedata']:  # iterate over defined routes
                    if a['route'] == r['route']:  # match on route number
                        new_nm = a['nm'].split(' ', 1)[1]
                        system_map.route_descriptions['routedata'][r]['nm'] = new_nm # update nm in system_map

                        # for k,v in a.items():  # then iterate over API response keys
                        #     try:
                        #         if r[k] != v:  # if the value from the API response is different
                        #             r[k] = v.split(' ', 1)[1]  # update the defined routes value with the API response one, splitting the route number off the front
                        #     except: # if the r[k] key is missing
                        #         r[k] = v.split(' ', 1)[1]


            # 6. make one last scan of system_map.route_descriptions -- if prettyname is blank, should copy nm to prettyname
            for route in system_map.route_descriptions['routedata']:
                if route['prettyname'] == "":
                    route['prettyname'] = route['nm']

            # 7. create data to dump with last_updated and ttl
            outdata = dict()
            now = datetime.datetime.now()
            outdata['last_updated'] = now.strftime("%Y-%m-%d %H:%M:%S")
            outdata['ttl'] = '86400'
            outdata['routedata'] = system_map.route_descriptions['routedata']
            # delete existing route_definition.json and dump new complete as a json
            with open('config/route_descriptions.json','w') as f:
                json.dump(outdata, f, indent=4)

            return

        else:
            print ('didnt update route_descriptions.json for some reason')
            return

class BunchingReport(Generator): # todo 0 test bunching_report

    def generate_reports(self, system_map):

        for r in system_map.route_descriptions['routedata']:
            route = r['route']

            report = {'rt':route, 'report':
                        {'type':'bunching',
                         'created_timestamp':(datetime.datetime.now)
                         }
                      }

            with self.db as db:
                # generates top 10 list of stops on the route by # of bunching incidents for period
                bunching_leaderboard = []
                cum_arrival_total = 0
                cum_bunch_total = 0

                for service in system_map.get_single_route_Paths(self, route):
                    for stop in service.stops: # bug this is probably wrong property to subscript
                        # first query to make sure there are ScheduledStop instances
                        bunch_total = 0
                        arrival_total = 0
                        report = StopReport(system_map, route, stop.identity, 'day')
                        for (index, row) in report.arrivals_list_final_df.iterrows():
                            arrival_total += 1
                            if (row.delta > report.bigbang) and (row.delta <= report.bunching_interval):
                                bunch_total += 1
                        cum_bunch_total = cum_bunch_total+bunch_total
                        cum_arrival_total = cum_arrival_total + arrival_total
                        bunching_leaderboard.append((stop.st, bunch_total,stop.identity))
                bunching_leaderboard.sort(key=itemgetter(1), reverse=True)
                report['report']['data'] = bunching_leaderboard[:10]

                self.store_pickle(report)

    def fetch_report(self, route):
        return self.retrieve_pickle(route,'bunching')

class GradeReport(Generator): # todo 1 write GradeReport generator

    def __init__(self, system_map):
        super(GradeReport,self).__init__()
        pass

    def generate_reports(self, period):
        return

        # # compute grade
        # # based on pct of all stops on route during period that were bunched
        # try:
        #     grade_numeric = (cum_bunch_total / cum_arrival_total) * 100
        #     for g in self.grade_descriptions:
        #         if g['bounds'][0] < grade_numeric <= g['bounds'][1]:
        #             self.grade = g['grade']
        #             self.grade_description = g['description']
        # except:
        #     self.grade = 'N/A'
        #     self.grade_description = 'Unable to determine grade.'
        #     pass
        #
        # time_created = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # bunching_leaderboard_pickle = dict(bunching_leaderboard=bunching_leaderboard, grade=self.grade,
        #                                    grade_numeric=grade_numeric, grade_description=self.grade_description, time_created=time_created)
        # outfile = ('data/bunching_leaderboard_'+route+'.pickle')
        # with open(outfile, 'wb') as handle:
        #     pickle.dump(bunching_leaderboard_pickle, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def fetch_report(self, period):
        try:
            x = 2
            y = 1
            y > x
            return

            # and B. number of bunching incidents


            # LOAD THE GRADE DESCRIPTION

            # method1
            # grade_description = next((item for item in self.grade_descriptions if item["grade"] == grade), None)

            # method2
            # grade_description2 = list(filter(lambda letter: letter['grade'] == grade, self.grade_descriptions))

            # method3
            # for letter in self.grade_descriptions:
            #     try letter['grade'] == grade:
            #         grade_description = letter['description']
            #     else:
            #         grade_description = 'No grade description available.'

            # grade = 'B'
            # grade_description = "This isn't working."
            # return grade, grade_description
            #
            #  future: based on average headway standard deviation

            # We can also report variability using standard deviation and that can be converted to a letter
            # (e.g.A is < 1 s.d., B is 1 to 1.5, etc.)
            # Example: For a headway of 20 minutes, a service dependability grade of B means 80 percent of the time the bus will come every 10 to 30 minutes.
            # for each (completed trip) in (period)
            #   for each (stop) on (trip)
            #       if period = now
            #           what is the average time between the last 2-3 arrivals
            #       elif period = anything else
            #           what is the average time between all the arrivals in the period

        except:
            grade = 'F'
            grade_description = "This isn't working."
            return grade, grade_description

class HeadwayReport(Generator): # future rewrite headway report

    def __init__(self, system_map):
        super(HeadwayReport,self).__init__()
        pass

    def f_timing(self, stop_df):
        stop_df['delta'] = (stop_df['arrival_timestamp'] - stop_df['arrival_timestamp'].shift(1)).fillna(
            0)  # calc interval between last bus for each row, fill NaNs
        stop_df = stop_df.dropna()  # drop the NaN (probably just the first one)
        return stop_df

    def generate_headway_report(self, system_map):

        with SQLAlchemyDBConnection() as db:

            # build the query
            x, trips_on_road_now = self.__get_current_trips()

            query = db.session.query(ScheduledStop). \
                add_columns(ScheduledStop.trip_id,
                            ScheduledStop.stop_id,
                            ScheduledStop.stop_name,
                            ScheduledStop.arrival_timestamp)

            # example of multi-table query -- would it require re-setting the relationships in DataBases.py class definitions?
            # # query = df.session.query(Trip, ScheduledStop, BusPosition).join(ScheduledStop).join(BusPosition)

            # add the period
            query = self.__query_factory(db, query,
                                         period=self.period)
            # # add extra filters -- EXCLUDES current trips
            # query=query\
            #     .filter(ScheduledStop.trip_id.notin_(trips_on_road_now))\
            #     .order_by(ScheduledStop.trip_id.asc())\
            #     .order_by(ScheduledStop.pkey.asc())\
            #     .statement

            # add extra filters -- INCLUDES current trips
            query = query \
                .order_by(ScheduledStop.trip_id.asc()) \
                .order_by(ScheduledStop.pkey.asc()) \
                .statement

            # execute query + if the database didn't have results, return an dummy dataframe
            arrivals_in_completed_trips = pd.read_sql(query, db.session.bind)
            if len(arrivals_in_completed_trips.index) == 0:
                arrivals_in_completed_trips = pd.DataFrame(
                    columns=['trip_id', 'stop_id', 'stop_name', 'arrival_timestamp'],
                    data=[['666_666_20100101', '38000', 'Dummy Stop', datetime.datetime(2010, 1, 1, 7, 0, 0)],
                          ['123_666_20100101', '38000', 'Dummy Stop', datetime.datetime(2010, 1, 1, 7, 10, 0)],
                          ['666_666_20100101', '38001', 'Dummy Stop', datetime.datetime(2010, 1, 1, 7, 10, 0)],
                          ['123_666_20100101', '38001', 'Dummy Stop', datetime.datetime(2010, 1, 1, 7, 21, 0)],
                          ['666_666_20100101', '38002', 'Dummy Stop', datetime.datetime(2010, 1, 1, 7, 20, 0)],
                          ['123_666_20100101', '38002', 'Dummy Stop', datetime.datetime(2010, 1, 1, 7, 28, 0)]]
                )

            # split by stop_id and calculate arrival intervals at each stop
            stop_dfs = [g for i, g in arrivals_in_completed_trips.groupby(
                arrivals_in_completed_trips['stop_id'].ne(arrivals_in_completed_trips['stop_id'].shift()).cumsum())]
            headways_df = pd.DataFrame()

            for stop_df in stop_dfs:  # iterate over every stop
                headways_df = headways_df.append(self.f_timing(stop_df))  # dump all these rows into the headways list

            # assemble the results and return
            headway = dict()
            # average headway for route -- entire period
            headway['period_mean'] = headways_df['delta'].mean()
            headway['period_std'] = headways_df['delta'].std()

            # average headway for route -- by hour
            times = pd.DatetimeIndex(headways_df.arrival_timestamp)
            # hourly_arrival_groups = headways_df.groupby([times.hour, times.minute])
            hourly_arrival_groups = headways_df.groupby([times.hour])
            headway['hourly_table'] = list()

            for hourly_arrivals in hourly_arrival_groups:
                df_hourly_arrivals = hourly_arrivals[1]  # grab the df from the tuple
                hour = datetime.time(7)

                # try this https://stackoverflow.com/questions/45239742/aggregations-for-timedelta-values-in-the-python-dataframe
                mean = df_hourly_arrivals.delta.mean(numeric_only=False)
                std = df_hourly_arrivals.delta.std(numeric_only=False)

                # compute the summary stats using numpy per https://stackoverflow.com/questions/44616546/finding-the-mean-and-standard-deviation-of-a-timedelta-object-in-pandas-df
                # mean2 = df_hourly_arrivals.delta.apply(lambda x: np.mean(x))
                # std2 = df_hourly_arrivals.delta.apply(lambda x: np.std(x))

                headway['hourly_table'].append((hour, mean, std))

            # to do average headway -- by hour, by stop

            return headway
        return

class TraveltimeReport(Generator): # future write traveltime reportt

    def __init__(self, system_map):
        super(TraveltimeReport,self).__init__()
        pass

    def get_traveltime(self, period):

        with SQLAlchemyDBConnection() as db:
            traveltime = dict()

            # # get a list of all COMPLETED trips on this route for this period
            #
            # todays_date = datetime.date.today()
            # yesterdays_date = datetime.date.today() - datetime.timedelta(1)
            # one_hour_ago = datetime.datetime.now() - datetime.timedelta(hours=1)
            #
            # x, trips_on_road_now = self.__get_current_trips()
            #
            #

            # elif self.period == 'today':
            #     arrivals_in_completed_trips = pd.read_sql(
            #         db.session.query(ScheduledStop.trip_id,
            #                          ScheduledStop.stop_id,
            #                          ScheduledStop.stop_name,
            #                          ScheduledStop.arrival_timestamp)
            #             .filter(ScheduledStop.arrival_timestamp != None)
            #             .filter(func.date(ScheduledStop.arrival_timestamp) == todays_date)
            #             .filter(ScheduledStop.trip_id.notin_(trips_on_road_now))
            #             .order_by(ScheduledStop.trip_id.asc())
            #             .order_by(ScheduledStop.arrival_timestamp.asc())
            #             .statement,
            #         db.session.bind)
            #
            #
            #
            #
            # # now, using pandas, find the difference in arrival_timestamp between first and last row of each group
            #
            # # Group the data frame by month and item and extract a number of stats from each group
            #
            # trip_start_end_times = arrivals_in_completed_trips.groupby("trip_id").agg({"arrival_timestamp": "min", "arrival_timestamp": "max"})
            #
            # travel_times = []
            # # now calculate the duration of the min:max tuples in trip_start_end_times, then average of those
            # for min,max in trip_start_end_times:
            #     travel_times.append(str(max-min))
            # traveltime['time'] = '%.0f' % (sum(travel_times) / float(len(travel_times))

            traveltime['time'] = 20

            return traveltime

