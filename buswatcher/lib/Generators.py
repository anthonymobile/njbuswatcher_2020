from pathlib import Path
import pickle
from operator import itemgetter
import json
from dateutil import parser
from datetime import timedelta
from sqlalchemy import func, text

import pandas as pd

from lib.wwwAPI import StopReport
from lib.BusAPI import *
from lib.DataBases import SQLAlchemyDBConnection, ScheduledStop, Trip
from lib.CommonTools import get_config_path

class Generator():

    def __init__(self):
        self.config_prefix = get_config_path()+"reports"
        self.db =  SQLAlchemyDBConnection()

    def store_json(self, report_to_store): # filename format route_type_period
        filename = ('{a}/{b}_{c}_{d}.json').format(a=self.config_prefix,b=report_to_store['route'],c=report_to_store['type'],d=report_to_store['period'])
        with open(filename, 'w') as f:
            json.dump(report_to_store, f, sort_keys=True,indent=4)
        return

    def retrieve_json(self, route, type, period):
        filename = ('{a}/{b}_{c}_{d}.json').format(a=self.config_prefix, b=route,c=type, d=period)
        with open(filename,"r") as f:
            report_retrieved = json.load(f)
        return report_retrieved

class RouteUpdater():

    def __init__(self,system_map):
        self.refresh_routedata(system_map)

    def refresh_routedata(self, system_map):
        now = datetime.datetime.now()

        # even though this now runs on a daily schedule
        # load existing reports and check ttl anyways
        try:
            # if os.getcwd() == "/":  # docker
            #     prefix = "/buswatcher/buswatcher/"
            # elif "Users" in os.getcwd():
            #     prefix = ""
            # else:
            #     prefix = ""
            prefix=get_config_path()
            with open(prefix+'route_descriptions.json') as f:
                route_descriptions_file = json.load(f)
            route_descriptions_last_updated = parser.parse(route_descriptions_file['last_updated'])

        except:
            route_descriptions_last_updated = parser.parse('2000-01-01 01:01:01')

        route_descriptions_ttl = timedelta(seconds=int(system_map.route_descriptions['ttl']))

        expired = False

        # if TTL expired, update route geometry local XMLs
        if (now - route_descriptions_last_updated) > route_descriptions_ttl:

            expired = True
            print ('Updating XML route definitions from remote source (NJTransit API getRoutePoints.jsp)')

            # UPDATE ROUTES FROM API

            # 1. list all routes from current definitions file and sort it by route number
            routelist_from_file = sorted([r['route'] for r in route_descriptions_file['routedata']])

            # 2. grab current buses list and see if there's any route #s we don't know yet

            # get list of active routes
            buses = parse_xml_getBusesForRouteAll(get_xml_data('nj', 'all_buses'))
            routelist_from_api_active = [b.rt for b in buses]
            # remove any bus not on a numeric route
            routes_active = list()
            for b in routelist_from_api_active:
                try:
                    dummy = int(b)
                    routes_active.append(b)
                except:
                    continue
            routes_active=list(set(routes_active))
            routes_active=sorted(routes_active)

            # merge the two and remove duplicates
            merged_routelist =sorted(list(set(routelist_from_file + routes_active)))

            # 3. create blank system_map.route_descriptions entries for any newly seen routes

            new_routes = [x for x in routes_active if x not in routelist_from_file]

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

                    # fetch data
                    xml_data = get_xml_data('nj', 'routes', route=r)

                    #dump it to disk
                    if expired == True: # but only if the files are older than the ttl
                        print (r)
                        outfile = ('config/route_geometry/' + r + '.xml')
                        with open(outfile, 'wb') as f:  # overwrite existing file
                            f.write(xml_data)

                    #parse it
                    parsed_route_xml = parse_xml_getRoutePoints(xml_data)
                    route_entry = {'route': parsed_route_xml[0][0].identity, 'nm': parsed_route_xml[0][0].nm}
                    api_response.append(route_entry)
                except:
                    continue

            # 5. merge API data into system_map.route_descriptions
            for a in api_response: # iterate over routes fetched from API
                for index,r in enumerate(system_map.route_descriptions['routedata']):  # iterate over defined routes
                    if a['route'] == r['route']:  # match on route number
                        new_nm = a['nm'].split(' ', 1)[1]
                        system_map.route_descriptions['routedata'][index]['nm'] = new_nm

                        # future more comprehensive mapping of API response to route_descriptions.json
                        # for k,v in a.items():  # then iterate over API response keys
                        #     try:
                        #         if r[k] != v:  # if the value from the API response is different
                        #             r[k] = v.split(' ', 1)[1]  # update the defined routes value with the API response one, splitting the route number off the front
                        #     except: # if the r[k] key is missing
                        #         r[k] = v.split(' ', 1)[1]


            # 6. make one last scan of system_map.route_descriptions -- if prettyname is blank, should copy nm to prettyname
            for index, r in enumerate(system_map.route_descriptions['routedata']):
                if r['prettyname'] == "":
                    system_map.route_descriptions['routedata'][r]['prettyname'] = r['nm']

            # 7. create data to dump with last_updated and ttl
            outdata = dict()
            now = datetime.datetime.now()
            outdata['last_updated'] = now.strftime("%Y-%m-%d %H:%M:%S")
            outdata['ttl'] = '86400'
            outdata['routedata'] = system_map.route_descriptions['routedata'] # ? sort the routes inside this dict -->  https://www.pythoncentral.io/how-to-sort-python-dictionaries-by-key-or-value/
            # delete existing route_definition.json and dump new complete as a json
            with open('config/route_descriptions.json','w') as f:
                json.dump(outdata, f, indent=4)

            return

        else:
            print ('didnt update route_descriptions.json because ttl not expired')
            return

class BunchingReport(Generator):

    def __init__(self):
        super(BunchingReport,self).__init__()
        self.type='bunching'

    def generate_reports(self, system_map):

        for r in system_map.route_descriptions['routedata']: # loop over all routes
            route = r['route']
            print ('route {a}'.format(a=route))

            for period in system_map.period_descriptions:  # loop over all periods
                print('\tperiod {a}'.format(a=period))

                bunching_report_template = {'route': route,
                          'type': 'bunching',
                          'period': period,
                          'created_timestamp': str((datetime.datetime.now))
                        }

                # make and dump the report -- the 10 stops with the most bunching incidents -- by route, by period
                with self.db as db:

                    bigbang = datetime.timedelta(seconds=0)
                    bunching_interval = datetime.timedelta(minutes=3)
                    bunching_leaderboard_raw = []
                    cum_arrival_total = 0
                    cum_bunch_total = 0

                    paths = system_map.get_single_route_Paths(route)[0][0].paths

                    for path in paths:
                        for point in path.points:
                            if isinstance(point,Route.Stop) is True:
                                 # first query to make sure there are ScheduledStop instances
                                bunch_total = 0
                                arrival_total = 0
                                stop_report = self.get_arrivals_here_this_route(system_map, route, point.identity, period)
                                for (index, row) in stop_report[0].iterrows():
                                    arrival_total += 1
                                    if (row.delta > bigbang) and (row.delta <= bunching_interval):
                                        bunch_total += 1
                                cum_bunch_total = cum_bunch_total+bunch_total
                                cum_arrival_total = cum_arrival_total + arrival_total
                                leaderboard_entry = {
                                                        'stop_name':point.st,
                                                        'stop_id':point.identity,
                                                        'bunched_arrivals_in_period':bunch_total
                                                     }

                                bunching_leaderboard_raw.append(leaderboard_entry)
                    # bunching_leaderboard.sort(key=itemgetter(1), reverse=True)
                    # https://stackoverflow.com/questions/72899/how-do-i-sort-a-list-of-dictionaries-by-a-value-of-the-dictionary
                    bunching_leaderboard = sorted(bunching_leaderboard_raw, key=lambda k: k['bunched_arrivals_in_period']) # bug sort in the other direction?

                    # log the results and dump
                    # bunching_report_template['bunching_leaderboard'] = bunching_leaderboard[:10] # bug take the other end?
                    bunching_report_template['bunching_leaderboard'] = bunching_leaderboard[10:]
                    bunching_report_template['cum_bunch_total'] = cum_bunch_total
                    bunching_report_template['cum_arrival_total'] = cum_arrival_total
                    self.store_json(bunching_report_template)

    ####################################################################################################
    # THIS CODE BLOCK IS AN ADAPTED DUPLICATE OF wwwAPI.StopReport.get_arrivals_here_this_route
    # future refactor to remove duplication
    ####################################################################################################

    def get_arrivals_here_this_route(self,system_map, route, stop_id, period):
        with SQLAlchemyDBConnection() as db:

            # build query and load into df
            query=db.session.query(Trip.rt, # base query
                                        Trip.v,
                                        Trip.pid,
                                        Trip.trip_id,
                                        ScheduledStop.stop_id,
                                        ScheduledStop.stop_name,
                                        ScheduledStop.arrival_timestamp) \
                                        .join(ScheduledStop) \
                                        .filter(Trip.rt == route) \
                                        .filter(ScheduledStop.stop_id == stop_id) \
                                        .filter(ScheduledStop.arrival_timestamp != None) \
                                        .order_by(ScheduledStop.arrival_timestamp.asc())

            query=self.query_factory(system_map, db, query, period=period) # add the period
            query=query.statement
            try:
                arrivals_here_this_route=pd.read_sql(query, db.session.bind)
                if len(arrivals_here_this_route.index) == 0: # no results return dummy df
                    return self.return_dummy_arrivals_df()
                else:
                    return self.filter_arrivals(arrivals_here_this_route)
            except ValueError: # any error return a dummy df
                return self.return_dummy_arrivals_df()

    def query_factory(self, system_map, db, query, **kwargs):
        query = query.filter(ScheduledStop.arrival_timestamp != None). \
            filter(ScheduledStop.arrival_timestamp >= func.ADDDATE(func.CURRENT_TIMESTAMP(), text(system_map.period_descriptions[kwargs['period']]['sql'])))
        return query

    def return_dummy_arrivals_df(self):
        # to add more than one , simply add to the lists
        dummydata = {'rt': ['0','0'],
                     'v': ['0000','0000'],
                     'pid': ['0','0'],
                     'trip_id': ['0000_000_00000000','0000_000_00000000'],
                     'stop_name': ['N/A','N/A'],
                     'arrival_timestamp': [datetime.time(0, 1),datetime.time(0, 1)],
                     'delta': datetime.timedelta(seconds=0)
                    }
        arrivals_list_final_df = pd.DataFrame(dummydata, columns=['rt','v','pid','trip_id','stop_name','arrival_timestamp','delta'])
        stop_name = 'N/A'
        self.arrivals_table_time_created = datetime.datetime.now()  # log creation time and return
        return arrivals_list_final_df, stop_name, self.arrivals_table_time_created

    def filter_arrivals(self, arrivals_here):
            # Otherwise, cleanup the query results -- split by vehicle and calculate arrival intervals

            # split final approach history (sorted by timestamp) at each change in vehicle_id into a list of dfs - per https://stackoverflow.com/questions/41144231/python-how-to-split-pandas-dataframe-into-subsets-based-on-the-value-in-the-fir
            final_approach_dfs = [g for i, g in arrivals_here.groupby(arrivals_here['v'].ne(arrivals_here['v'].shift()).cumsum())]

            # take the last V(ehicle) approach in each df and add it to final list of arrivals
            arrivals_list_final_df = pd.DataFrame()
            for final_approach in final_approach_dfs:  # iterate over every final approach
                arrival_insert_df = final_approach.tail(1)  # take the last observation
                arrivals_list_final_df = arrivals_list_final_df.append(arrival_insert_df)  # insert into df

            try:
                # calc interval between last bus for each row, fill NaNs #
                arrivals_list_final_df['delta'] = (arrivals_list_final_df['arrival_timestamp'] - arrivals_list_final_df['arrival_timestamp'].shift(1)).fillna(pd.Timedelta(seconds=0))
            except:
                arrivals_list_final_df['delta'] = ''
                print('')

            try:
                stop_name = arrivals_list_final_df['stop_name'].iloc[0]
            except:
                stop_name = 'N/A'

            arrivals_table_time_created = datetime.datetime.now()  # log creation time and return

            return arrivals_list_final_df, stop_name, arrivals_table_time_created

    ####################################################################################################
    # ^^^^^^^THIS CODE BLOCK IS AN ADAPTED DUPLICATE OF wwwAPI.StopReport.get_arrivals_here_this_route
    ####################################################################################################

# sample bunching report
'''
{
    "rt": "119",
    "type": "bunching",
    "period": "day",
    "created_timestamp": "2019-06-34 02:23:22",
    "bunching_leaderboard": [
        {
         'stop_name':'STREET AND STREET',
          'stop_id':'31822',
          'bunched_arrivals_in_period':'54'
          },
        {
         'stop_name':'STREET AND STREET',
          'stop_id':'31822',
          'bunched_arrivals_in_period':'54'
          },
          {
         'stop_name':'STREET AND STREET',
          'stop_id':'31822',
          'bunched_arrivals_in_period':'54'
          }
          ],
    "cum_bunch_total": "45",
    "cum_arrival_total": "450"
}

        


'''


class GradeReport(Generator):

    def __init__(self):
        super(GradeReport,self).__init__()
        self.type='grade'

    def generate_reports(self, system_map):

        for r in system_map.route_descriptions['routedata']:  # loop over all routes
            route = r['route']

            for period in system_map.period_descriptions:  # loop over all periods

                report = {'route': route,
                          'type': 'grade',
                          'period': period,
                          'created_timestamp': str((datetime.datetime.now))
                     }


                # make and pickle the report

                # 1. load the bunching report and compute the absolute number of arrivals, number bunched, percent, and assign a letter grade based on grade_descriptions

                try:
                    bunching_report_fetched = self.retrieve_json(route, 'bunching', period)
                except FileNotFoundError: # if the file doesn't exist quit this report and try next period
                    continue

                # compute grade based on pct of all stops on route during period that were bunched
                try:
                    grade_numeric = (bunching_report_fetched['cum_bunch_total'] / bunching_report_fetched['cum_arrival_total']) * 100
                    for g,g_desc in system_map.grade_descriptions.items():
                        if (grade_numeric >= float(g_desc['bounds'][0])) and (grade_numeric < float(g_desc['bounds'][1])):
                                grade = g_desc['grade']
                                grade_description = g_desc['description']
                                break

                except:
                    grade = 'N/A'
                    grade_description = 'Unable to determine grade.'
                    pass

                # 2. set the report results
                report['grade'] = grade
                report['grade_description'] =  grade_description,
                report['pct_bunched'] = grade_numeric


                # 3. dump it

                self.store_json(report)


        return

# sample grade report
'''
{
    "rt": "119",
    "type": "grade",
    "period": "day",
    "created_timestamp": "2019-06-34 02:23:22",
    "grade": "B",
    "grade_description": "Something loaded from grade_descriptons.json",
    "pct_bunched": "10.0"
}

'''



class HeadwayReport(Generator): # future rewrite headway report

    def __init__(self):
        super(HeadwayReport,self).__init__()
        self.type='headway'

    def f_timing(self, stop_df):
        stop_df['delta'] = (stop_df['arrival_timestamp'] - stop_df['arrival_timestamp'].shift(1)).fillna(
            0)  # calc interval between last bus for each row, fill NaNs
        stop_df = stop_df.dropna()  # drop the NaN (probably just the first one)
        return stop_df

    def generate_reports(self, system_map):

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
        self.type='traveltime'

    def generate_reports(self, period):

        with SQLAlchemyDBConnection() as db:
            traveltime = dict()

            # # get a list of all COMPLETED trips on this route for this period
            #
            # todays_date = datetime.date.today()
            # yesterdays_date = datetime.date.today() - datetime.timedelta(1)
            # one_hour_ago = datetime.datetime.now() - datetime.timedelta(hours=1)
            #
            # x, trips_on_road_now = self.get_current_trips()
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

