import datetime
import json
import os
import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import func, text

from . import NJTransitAPI
from .DataBases import SQLAlchemyDBConnection, Trip, BusPosition, Stop



def get_route_summary(route):

    return pd.read_csv('data/_df_route_summary.csv') # todo generate this here, or read this file made by Generator


class GenericReport: # all Report classes inherit query_factory

    def query_factory(self, db, query, **kwargs):
        query = query.filter(Stop.arrival_timestamp != None). \
            filter(Stop.arrival_timestamp >= func.ADDDATE(func.CURRENT_TIMESTAMP(), text(self.period_descriptions[self.period]['sql'])))

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

        # create database connection
        self.db = SQLAlchemyDBConnection()

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
        self.grade_report = self.retrieve_json('grade')
        # self.headway_report = self.retrieve_json('headay')
        # self.traveltime_report = self.retrieve_json('traveltime')


    def get_current_trips(self):
        # get a list of trips current running the route
        v_on_route = NJTransitAPI.parse_xml_getBusesForRoute(
            NJTransitAPI.get_xml_data(self.source, 'buses_for_route', route=self.route))
        todays_date = datetime.datetime.today().strftime('%Y%m%d')
        trip_list = list()
        trip_list_trip_id_only = list()

        for v in v_on_route:
            trip_id = ('{a}_{b}_{c}').format(a=v.id, b=v.run, c=todays_date)
            trip_list.append((trip_id, v.pd, v.bid, v.run))
            trip_list_trip_id_only.append(trip_id)

        return trip_list, trip_list_trip_id_only

    # populates the undermap trip dash
    def get_tripdash(self):
        # gets most recent stop for all active vehicles on route, only if they were observed in the last 5 minutes
        with self.db as db:

            trip_list, x = self.get_current_trips()

            tripdash = dict()
            for trip_id,pd,bid,run in trip_list:

                five_mins_ago = datetime.datetime.now() - datetime.timedelta(minutes=5)

                # OLD
                # load the trip card - limit 1
                most_recent_stop = db.session.query(Stop) \
                    .join(Trip) \
                    .filter(Trip.trip_id == trip_id) \
                    .filter(Stop.arrival_timestamp != None) \
                    .filter(Stop.arrival_timestamp < five_mins_ago) \
                    .order_by(Stop.arrival_timestamp.desc()) \
                    .limit(1) \
                    .all()
                trip_dict=dict()
                try:
                    trip_dict['stoplist']=[most_recent_stop[0]]
                except:
                    trip_dict['stoplist']=[]

                trip_dict['pd'] = pd
                trip_dict['v'] = bid
                trip_dict['run'] = run
                tripdash[trip_id] = trip_dict

        return tripdash


    def retrieve_json(self, type):
        file_prefix = Path(os.getcwd() + "/config/reports/")
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

            if type=='grade':
                report_retrieved['grade'] = 'N'
                report_retrieved['grade_description'] = 'No description available.'
                report_retrieved["pct_bunched"] = "10.0"
            elif type=='bunching':
                report_retrieved['bunching_leaderboard'] = [
                    {'stop_name': 'STREET AND STREET',
                        'stop_id': '31822',
                        'bunched_arrivals_in_period': '666'
                    }]
                report_retrieved['cum_bunch_total'] = '45'
                report_retrieved['cum_arrival_total'] = '450'
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

        # create database connection
        self.db = SQLAlchemyDBConnection()

        # constants
        self.bunching_interval = datetime.timedelta(minutes=3)
        self.bigbang = datetime.timedelta(seconds=0)
        # self.stop_name =self.get_stop_name()

        # populate data for webpage
        self.arrivals_here_this_route_df, self.stop_name, self.arrivals_table_time_created = self.get_arrivals_here_this_route()
        self.arrivals_here_all_others = self.get_arrivals_here_all_others()
        self.hourly_frequency = self.get_hourly_frequency()


    def get_arrivals_here_this_route(self):
        with self.db as db:

            # build query and load into df
            query=db.session.query(Trip.rt,  # base query
                                   Trip.v,
                                   Trip.pid,
                                   Trip.trip_id,
                                   Stop.stop_id,
                                   Stop.stop_name,
                                   Stop.arrival_timestamp) \
                                        .join(Stop) \
                                        .filter(Trip.rt == self.route) \
                                        .filter(Stop.stop_id == self.stop_id) \
                                        .filter(Stop.arrival_timestamp != None) \
                                        .order_by(Stop.arrival_timestamp.asc())

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
        with self.db as db:
            query = db.session.query(Trip.rt,  # base query
                                     Trip.v,
                                     Trip.pd,
                                     Stop.stop_id,
                                     Stop.stop_name,
                                     Stop.arrival_timestamp) \
                .join(Stop) \
                .filter(Stop.stop_id == self.stop_id) \
                .filter(Stop.arrival_timestamp != None)

            query = self.query_factory(db, query, period=self.period)  # add the period
            query = query.filter(Trip.rt != self.route) # exclude the current route
            query = query.statement
            try:
                get_arrivals_here_all_others = pd.read_sql(query, db.session.bind)
                return get_arrivals_here_all_others.head(20)
            except ValueError:
                pass

    def filter_arrivals(self, arrivals_here):
            # Otherwise, cleanup the query results -- split by vehicle and calculate arrival intervals

            # speedup by using slice vs groupby
            # alex r says:
            # for group in df['col'].unique():
            #     slice = df[df['col'] == group]
            # # is like 10x faster than
            # df.groupby('col').apply( < stuffhere >)

            # split final approach history (sorted by timestamp) at each change in vehicle_id outputs a list of dfs - per https://stackoverflow.com/questions/41144231/python-how-to-split-pandas-dataframe-into-subsets-based-on-the-value-in-the-fir
            final_approach_dfs = [g for i, g in arrivals_here.groupby(arrivals_here['v'].ne(arrivals_here['v'].shift()).cumsum())]
            arrivals_list_final_df = pd.DataFrame()  # take the last V(ehicle) approach in each df and add it to final list of arrivals
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

            # one last sort to make the table most recent at top
            arrivals_list_final_df = arrivals_list_final_df.sort_values('arrival_timestamp', ascending=False)

            return arrivals_list_final_df.head(50), stop_name, arrivals_table_time_created

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
        self.arrivals_here_this_route_df['delta_interval_seconds'] = self.arrivals_here_this_route_df['delta'].dt.seconds
        try:
            df_tmp=self.arrivals_here_this_route_df.set_index('arrival_timestamp')
            results = (df_tmp.groupby(df_tmp.index.hour).mean()) // 60
            results = results.rename(columns={'delta_interval_seconds': 'frequency'})
            results['hour'] = results.index
        except AttributeError:
            results = pd.DataFrame()
        return results


class TripReport(GenericReport):
    #################################################################################
    # TRIP REPORT                                               TRIP REPORT
    #################################################################################

    def __init__(self, system_map, route, trip_id):
        # apply passed parameters to instance
        self.source = 'nj'
        self.route = route
        self.trip_id = trip_id
        self.v = trip_id.split('_')[0]

        # create database connection
        self.db = SQLAlchemyDBConnection()

        # populate data for webpage
        self.triplog=self.get_triplog()

    def get_triplog(self):
        # gets most recent stop for all active vehicles on route
        # can grab more by changing from .one() to .limit(10).all()
        with self.db as db:

            todays_date = datetime.datetime.today().strftime('%Y%m%d')

            # grab the latest list of buses active on this route from the NJT API
            v_on_route = NJTransitAPI.parse_xml_getBusesForRoute(
                NJTransitAPI.get_xml_data(self.source, 'buses_for_route', route=self.route))
            # pluck ours out
            for v in v_on_route:
                trip_id = ('{a}_{b}_{c}').format(a=v.id, b=v.run, c=todays_date)
                if trip_id == self.trip_id:
                    trip_metadata = {'pd':v.pd,'id':v.id,'run':v.run}

            # build the trip card
            trip_dict=dict()
            # all stops including missed ones

            # since = datetime.now() - timedelta(hours=24)
            # q = (session.query(Product).filter(or_(
            #     Product.last_time_parsed == None,
            #     Product.last_time_parsed < since)))
            #

            # grab all stop arrivals in the last 90 minutes
            # ninety_mins_ago = datetime.datetime.now() - datetime.timedelta(minutes=90)
            # trip_dict['stoplist']= \
            #     db.session.query(Stop) \
            #         .join(Trip) \
            #         .filter(Trip.trip_id == self.trip_id) \
            #         .filter(Stop.arrival_timestamp < ninety_mins_ago  ) \
            #         .order_by(Stop.pkey.asc()) \
            #         .all()
            trip_dict['stoplist']= \
                db.session.query(Stop) \
                    .join(Trip) \
                    .filter(Trip.trip_id == self.trip_id) \
                    .order_by(Stop.pkey.asc()) \
                    .all()

            trip_dict['pd'] = trip_metadata['pd']
            trip_dict['v'] = trip_metadata['id']
            trip_dict['run'] = trip_metadata['run']

            # and return
            triplog = dict()
            triplog[self.trip_id] = trip_dict

        return triplog
