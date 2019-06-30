import datetime
import pandas as pd
from sqlalchemy import func, text

from . import BusAPI
from .DataBases import SQLAlchemyDBConnection, Trip, BusPosition, ScheduledStop
from .Generators import *

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

        self.route_geometry = system_map.route_geometries[self.route] # RouteConfig.get_route_geometry(system_map,route)

        self.routes, self.coordinate_bundle = system_map.get_single_route_paths_and_coordinatebundle(self.route) # BusAPI.parse_xml_getRoutePoints(RouteConfig.get_route_geometry(self.route))
        self.routename, self.waypoints_coordinates, self.stops_coordinates, self.waypoints_geojson, self.stops_geojson = \
            self.routes[0].nm, self.coordinate_bundle['waypoints_coordinates'], self.coordinate_bundle['stops_coordinates'], \
            self.coordinate_bundle['waypoints_geojson'], self.coordinate_bundle['stops_geojson']
        self.route_stop_list = system_map.get_single_route_stoplist_for_wwwAPI(self.route)

        # query dynamic stuff
        self.trip_list, self.trip_list_trip_id_only = self.__get_current_trips()
        self.tripdash = self.get_tripdash()

        # and compute summary statistics
        self.active_bus_count = len(self.trip_list_trip_id_only)  # this is probably faster than fetching getBusesForRoute&rt=self.route from the NJT API

        # load Generators report
        self.bunching_report = BunchingReport.fetch_report(self.route) # todo 0 this is the template for the others
        self.grade,self.grade_description = GradeReport.fetch_report(self)
        # self.headway_report = HeadwayReport.fetch_headway_report(self)
        # self.traveltime_report = Generators.fetch_traveltime_report(self)


    def __get_current_trips(self):
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

            trip_list, x = self.__get_current_trips()

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
        self.arrivals_list_final_df, self.stop_name, self.arrivals_table_time_created = self.get_arrivals()
        self.arrivals_here_all_others = self.get_arrivals_here_all_others()
        self.hourly_frequency = self.get_hourly_frequency()


    def return_dummy_arrivals_df(self):
        # to add more than one , simply add to the lists
        dummydata = {'rt': ['0','0'],
                     'v': ['0000','0000'],
                     'pid': ['0','0'],
                     'trip_id': ['0000_000_00000000','0000_000_00000000'],
                     'stop_name': ['N/A','N/A'],
                     'arrival_timestamp': [datetime.time(0, 1),datetime.time(0, 1)]
                    }
        arrivals_list_final_df = pd.DataFrame(dummydata, columns=['rt','v','pid','trip_id','stop_name','arrival_timestamp'])
        stop_name = 'N/A'
        self.arrivals_table_time_created = datetime.datetime.now()  # log creation time and return
        return arrivals_list_final_df, stop_name, self.arrivals_table_time_created

    def get_arrivals(self):
        with SQLAlchemyDBConnection() as db:

            # build query and load into df
            query=db.session.query(Trip.rt, # base query # todo 0 add a sort by arrival_timestamp descending here?
                                        Trip.v,
                                        Trip.pid,
                                        Trip.trip_id,
                                        ScheduledStop.stop_id,
                                        ScheduledStop.stop_name,
                                        ScheduledStop.arrival_timestamp) \
                                        .join(ScheduledStop) \
                                        .filter(Trip.rt == self.route) \
                                        .filter(ScheduledStop.stop_id == self.stop_id) \
                                        .filter(ScheduledStop.arrival_timestamp != None)

            query=self.query_factory(db, query,period=self.period) # add the period
            query=query.statement
            try:
                arrivals_here=pd.read_sql(query, db.session.bind)
                if len(arrivals_here.index) == 0: # no results return dummy df
                    return self.return_dummy_arrivals_df()
                else:
                    return self.filter_arrivals(arrivals_here)
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
                return self.filter_arrivals(get_arrivals_here_all_others)[0] # [0] only return the dataframe from the self.filter_arrivals tuple
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

            try: # bug getting -24 hour time errors here, need to resort by timestamp again? # todo 0 or sort by arrival_timestamp descending here?
                # calc interval between last bus for each row, fill NaNs #
                arrivals_list_final_df['delta'] = (arrivals_list_final_df['arrival_timestamp'] - arrivals_list_final_df['arrival_timestamp'].shift(1)).fillna(0)
            except:
                arrivals_list_final_df['delta'] = float('nan')

            try:
                stop_name = arrivals_list_final_df['stop_name'].iloc[0]
            except:
                stop_name = 'N/A'

            arrivals_table_time_created = datetime.datetime.now()  # log creation time and return

            return arrivals_list_final_df, stop_name, arrivals_table_time_created

    def get_hourly_frequency(self):  # todo 00 get_hourly_frequency
        results = pd.DataFrame()
        self.arrivals_list_final_df['delta_int'] = self.arrivals_list_final_df['delta'].dt.seconds

        try:
            # results['frequency']= (self.arrivals_list_final_df.delta_int.resample('H').mean())//60
            results = (self.arrivals_list_final_df.groupby(self.arrivals_list_final_df.index.hour).mean())//60
            results = results.rename(columns={'delta_int': 'frequency'})
            results = results.drop(['pkey'], axis=1)
            results['hour'] = results.index

        except TypeError:
            pass

        except AttributeError:
            results = pd.DataFrame()

        return results


