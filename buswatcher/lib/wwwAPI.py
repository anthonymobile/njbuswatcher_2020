import datetime
import json
import os
from pathlib import Path

import pandas as pd
from sqlalchemy import func, text

from . import BusAPI
from .DataBases import SQLAlchemyDBConnection, Trip, BusPosition, ScheduledStop


class GenericReport: # all Report classes inherit query_factory

    def query_factory(self, db, query, **kwargs):
        query = query.filter(ScheduledStop.arrival_timestamp != None). \
            filter(ScheduledStop.arrival_timestamp >= func.ADDDATE(func.CURRENT_TIMESTAMP(), text(self.period_descriptions[self.period]['sql'])))

        return query


class RouteReport(GenericReport):
#################################################################################
# ROUTE REPORT                                                  ROUTE REPORT
#################################################################################

    class Path():
        def __init__(self):
            self.name = 'Path'
            self.stops = []
            self.id = ''
            self.d = ''
            self.dd = ''

    def __init__(self, system_map, route, period):

        # apply passed parameters to instance
        self.source='nj'
        self.route = route
        self.period = period
        self.period_descriptions = system_map.period_descriptions

        # load static stuff
        self.period_args = system_map.period_descriptions[self.period]

        # perishability
        self.time_created=datetime.datetime.now()
        self.ttl = 60 # seconds

        # populate route metadata and geometry from system_map -- these seems like awkward ways to do it (and to do it 4x?) but they work
        self.description_long = [x['description_long'] for x in system_map.route_descriptions['routedata'] if x['route'] == self.route][0]
        self.description_long = [x['description_short'] for x in system_map.route_descriptions['routedata'] if x['route'] == self.route][0]
        self.prettyname = [x['prettyname'] for x in system_map.route_descriptions['routedata'] if x['route'] == self.route][0]
        self.schedule_url = [x['schedule_url'] for x in system_map.route_descriptions['routedata'] if x['route'] == self.route][0]

        self.route_geometry = system_map.route_geometries[self.route]

        self.routes, self.coordinate_bundle = system_map.get_single_route_paths_and_coordinatebundle(self.route)
        self.routename, self.waypoints_coordinates, self.stops_coordinates, self.waypoints_geojson, self.stops_geojson = \
            self.routes[0].nm, self.coordinate_bundle['waypoints_coordinates'], self.coordinate_bundle['stops_coordinates'], \
            self.coordinate_bundle['waypoints_geojson'], self.coordinate_bundle['stops_geojson']
        self.route_stop_list = system_map.get_single_route_stoplist_for_wwwAPI(self.route)

        # query dynamic stuff
        self.trip_list, self.trip_list_trip_id_only = self.get_current_trips()
        self.tripdash = self.get_tripdash()

        # and compute summary statistics
        self.active_bus_count = len(self.trip_list_trip_id_only)

        # load Generators report
        self.bunching_report = self.retrieve_json('bunching')
        self.grade_report = self.retrieve_json('grade') # bug too many values to unpack
        # self.headway_report = self.retrieve_json('headay')
        # self.traveltime_report = self.retrieve_json('traveltime')


    def get_current_trips(self):
        # get a list of trips current running the route
        v_on_route = BusAPI.parse_xml_getBusesForRoute(
            BusAPI.get_xml_data(self.source, 'buses_for_route', route=self.route))
        todays_date = datetime.datetime.today().strftime('%Y%m%d')
        trip_list = list()
        trip_list_trip_id_only = list()

        for v in v_on_route:
            trip_id = ('{a}_{b}_{c}').format(a=v.id, b=v.run, c=todays_date)
            trip_list.append((trip_id, v.pd, v.bid, v.run))
            trip_list_trip_id_only.append(trip_id)

        return trip_list, trip_list_trip_id_only


    def get_tripdash(self):
        # gets all arrivals (see limit) for all runs on current route

        with SQLAlchemyDBConnection() as db:

            trip_list, x = self.get_current_trips()

            tripdash = dict()
            for trip_id,pd,bid,run in trip_list:

                # load the trip card - full with all the missed stops
                # scheduled_stops = db.session.query(ScheduledStop) \
                #     .join(Trip) \
                #     .filter(Trip.trip_id == trip_id) \
                #     .order_by(ScheduledStop.pkey.asc()) \
                #     .all()

                # load the trip card - limit 3
                scheduled_stops = db.session.query(ScheduledStop) \
                    .join(Trip) \
                    .filter(Trip.trip_id == trip_id) \
                    .filter(ScheduledStop.arrival_timestamp != None) \
                    .order_by(ScheduledStop.pkey.desc()) \
                    .limit(3) \
                    .all()

                trip_dict=dict()
                trip_dict['stoplist']=scheduled_stops
                trip_dict['pd'] = pd
                trip_dict['v'] = bid
                trip_dict['run'] = run
                tripdash[trip_id] = trip_dict

        return tripdash

    def retrieve_json(self, type):
        file_prefix = Path(os.getcwd() + "config/reports/")
        filename = ('{a}/{b}_{c}_{d}.json').format(a=file_prefix,b=self.route,c=type,d=self.period)

        try:
            with open(filename, "rb") as f:
                report_retrieved = json.load(f)
        except FileNotFoundError:
            report_retrieved = {
                "rt": self.route,
                "type": type,
                "period": self.period,
                "created_timestamp": datetime.datetime.now(),
                "dummy": "True"
            }









        return report_retrieved


class StopReport(GenericReport):
#################################################################################
# STOP REPORT                                               STOP REPORT
#################################################################################

    def __init__(self, system_map, route, stop, period):

        # apply passed parameters to instance
        self.source = 'nj'
        self.route = route
        self.stop_id = stop
        self.period = period
        self.period_descriptions = system_map.period_descriptions

        # constants
        self.bunching_interval = datetime.timedelta(minutes=3)
        self.bigbang = datetime.timedelta(seconds=0)
        # self.stop_name =self.get_stop_name()

        # populate data for webpage
        self.arrivals_here_this_route_df, self.stop_name, self.arrivals_table_time_created = self.get_arrivals_here_this_route()
        self.arrivals_here_all_others = self.get_arrivals_here_all_others()
        self.hourly_frequency = self.get_hourly_frequency()


    def get_arrivals_here_this_route(self):
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
                                        .filter(Trip.rt == self.route) \
                                        .filter(ScheduledStop.stop_id == self.stop_id) \
                                        .filter(ScheduledStop.arrival_timestamp != None) \
                                        .order_by(ScheduledStop.arrival_timestamp.desc()) # todo test this on stop page, if it helps fix the arrival interval 24 hours problem

            query=self.query_factory(db, query,period=self.period) # add the period
            query=query.statement
            try:
                arrivals_here_this_route=pd.read_sql(query, db.session.bind)
                if len(arrivals_here_this_route.index) == 0: # no results return dummy df
                    return self.return_dummy_arrivals_df()
                else:
                    return self.filter_arrivals(arrivals_here_this_route)
            except ValueError: # any error return a dummy df
                return self.return_dummy_arrivals_df()

    def get_arrivals_here_all_others(self):
        with SQLAlchemyDBConnection() as db:
            query = db.session.query(Trip.rt,  # base query
                                     Trip.v,
                                     Trip.pd,
                                     ScheduledStop.stop_id,
                                     ScheduledStop.stop_name,
                                     ScheduledStop.arrival_timestamp) \
                .join(ScheduledStop) \
                .filter(ScheduledStop.stop_id == self.stop_id) \
                .filter(ScheduledStop.arrival_timestamp != None)

            query = self.query_factory(db, query, period=self.period)  # add the period
            query = query.filter(Trip.rt != self.route) # exclude the current route
            query = query.statement
            try:
                get_arrivals_here_all_others = pd.read_sql(query, db.session.bind)
                return get_arrivals_here_all_others
            except ValueError:
                pass

    def filter_arrivals(self, arrivals_here):
            # Otherwise, cleanup the query results -- split by vehicle and calculate arrival intervals

            # future speedup by using slice vs groupby
            # alex r says:
            # for group in df['col'].unique():
            #     slice = df[df['col'] == group]
            # # is like 10x faster than
            # df.groupby('col').apply( < stuffhere >)

            # split final approach history (sorted by timestamp) at each change in vehicle_id outputs a list of dfs
            # per https://stackoverflow.com/questions/41144231/python-how-to-split-pandas-dataframe-into-subsets-based-on-the-value-in-the-fir
            final_approach_dfs = [g for i, g in arrivals_here.groupby(arrivals_here['v'].ne(arrivals_here['v'].shift()).cumsum())]
            arrivals_list_final_df = pd.DataFrame()  # take the last V(ehicle) approach in each df and add it to final list of arrivals
            for final_approach in final_approach_dfs:  # iterate over every final approach
                arrival_insert_df = final_approach.tail(1)  # take the last observation
                arrivals_list_final_df = arrivals_list_final_df.append(arrival_insert_df)  # insert into df

            try:
                # calc interval between last bus for each row, fill NaNs #
                # bug FutureWarning: Passing integers to fillna is deprecated, will raise a TypeError in a future version.  To retain the old behavior, pass pd.Timedelta(seconds=n) instead.
                arrivals_list_final_df['delta'] = (arrivals_list_final_df['arrival_timestamp'] - arrivals_list_final_df['arrival_timestamp'].shift(1)).fillna(0) # bug getting -24 hour time errors here, need to resort by timestamp again?
            except:
                arrivals_list_final_df['delta'] = ''
                print('')

            try:
                stop_name = arrivals_list_final_df['stop_name'].iloc[0]
            except:
                stop_name = 'N/A'

            arrivals_table_time_created = datetime.datetime.now()  # log creation time and return

            return arrivals_list_final_df, stop_name, arrivals_table_time_created

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


    def get_hourly_frequency(self):
        results = pd.DataFrame()
        self.arrivals_here_this_route_df['delta_int'] = self.arrivals_here_this_route_df['delta'].dt.seconds

        try:
            # results['frequency']= (self.arrivals_here_this_route_df.delta_int.resample('H').mean())//60
            results = (self.arrivals_here_this_route_df.groupby(self.arrivals_here_this_route_df.index.hour).mean()) // 60
            results = results.rename(columns={'delta_int': 'frequency'})
            results = results.drop(['pkey'], axis=1)
            results['hour'] = results.index

        except TypeError:
            pass

        except AttributeError:
            results = pd.DataFrame()

        return results


