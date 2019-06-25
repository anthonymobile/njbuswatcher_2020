import datetime
import pandas as pd

from sqlalchemy import func
import datetime_periods

import buswatcher.lib.BusAPI as BusAPI
import buswatcher.lib.Generators as Generators
from buswatcher.lib.DataBases import SQLAlchemyDBConnection, Trip, BusPosition, ScheduledStop
# from buswatcher.lib.DataBases import SQLAlchemyDBConnection, Trip, BusPosition, ScheduledStop

from buswatcher.lib.CommonTools import timeit


class GenericReport:

    # def __init__(self):
    #     pass

    def query_factory(self, db, query, **kwargs):

        now = datetime.datetime.now()
        # todays_date = datetime.date.today()
        # yesterdays_date = datetime.date.today() - datetime.timedelta(1)
        # one_hour_ago = datetime.datetime.now() - datetime.timedelta(hours=1)

        period_start = datetime_periods.period_beginning(now, self.period['name'])
        period_end = now # todo 99 this can also be passed in

        query = query.filter(ScheduledStop.arrival_timestamp != None).\
            filter(func.date(ScheduledStop.arrival_timestamp) >= period_start). \
            filter(func.date(ScheduledStop.arrival_timestamp) < period_end)

        #
        # if kwargs['period'] == 'now': # presently, 'now' is the same view as 'today'
        #     # query = query.filter(ScheduledStop.arrival_timestamp != None).filter(func.date(ScheduledStop.arrival_timestamp) > one_hour_ago)
        #     query = query.filter(ScheduledStop.arrival_timestamp != None).filter(func.date(ScheduledStop.arrival_timestamp) == todays_date)
        # elif kwargs['period'] == 'today':
        #     query = query.filter(ScheduledStop.arrival_timestamp != None).filter(func.date(ScheduledStop.arrival_timestamp) == todays_date)
        # elif kwargs['period'] == 'yesterday':
        #     query = query.filter(ScheduledStop.arrival_timestamp != None).filter(func.date(ScheduledStop.arrival_timestamp) == yesterdays_date)
        # elif kwargs['period'] == 'history':
        #     query = query.filter(ScheduledStop.arrival_timestamp != None)

        return query

class RouteReport(GenericReport):

    class Path():
        def __init__(self):
            self.name = 'Path'
            self.stops = []
            self.id = ''
            self.d = ''
            self.dd = ''

    # @timeit -- 0.2 seconds on the thinkcentre
    def __init__(self, system_map, route, period):

        # apply passed parameters to instance
        self.source='nj'
        self.route = route
        self.period = period

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
        self.route_stop_list = self.__get_stoplist(system_map)

        # query dynamic stuff
        self.trip_list, self.trip_list_trip_id_only = self.__get_current_trips()
        self.tripdash = self.get_tripdash()

        # and compute summary statistics
        self.active_bus_count = len(self.trip_list_trip_id_only)  # this is probably faster than fetching getBusesForRoute&rt=self.route from the NJT API

        # load Generators report
        self.bunching_report = Generators.fetch_bunching_report(self)
        self.headway_report = Generators.fetch_headway_report(self)
        self.traveltime_report = Generators.fetch_traveltime_report(self)
        self.grade,self.grade_description = Generators.fetch_grade_report(self)


    # def __get_period_labels(self):
    #     if self.period == 'now':
    #         period_label = "current"
    #     elif self.period == 'today':
    #         period_label = "today's"
    #     elif self.period == 'yesterday':
    #         period_label = "yesterday's"
    #     elif self.period == 'history':
    #         period_label = "forever's"
    #     else:
    #         period_label = '-no period label assigned-'
    #     return period_label

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

    def __get_stoplist(self,system_map): #todo 0 test and if it works, replace calls to this wrapper function with the get_single_route_stoplist_for_wwwAPI(route) one below

        return system_map.get_single_route_stoplist_for_wwwAPI(self.route)


        # OLD
        #
        # route_stop_list = []
        #
        # for direction in system_map.get_single_route_Paths(self.route)[0]: # for route in system_map.route_geometries_remote[self.route][0]:
        #     path_list = []
        #     for path in direction.paths:
        #         stops_points = RouteReport.Path()
        #         for point in path.points:
        #             if isinstance(point, BusAPI.Route.Stop):
        #                 stops_points.stops.append(point)
        #         stops_points.id = path.id
        #         stops_points.d = path.d
        #         stops_points.dd = path.dd
        #         path_list.append(
        #             stops_points)  # path_list is now a couple of Path instances, plus the metadata id,d,dd fields
        #     route_stop_list.append(path_list)
        #     return route_stop_list[0]  # transpose a single copy since the others are all repeats (can be verified by path ids)

        # EVEN OLDER
        #
        # routes, coordinate_bundle = BusAPI.parse_xml_getRoutePoints(self.route_geometry)
        # # routes, coordinate_bundle = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data(self.source, 'routes', route=self.route))
        # route_stop_list = []
        # for r in routes:
        #     path_list = []
        #     for path in r.paths:
        #         stops_points = RouteReport.Path()
        #         for point in path.points:
        #             if isinstance(point, BusAPI.Route.Stop):
        #                 stops_points.stops.append(point)
        #         stops_points.id = path.id
        #         stops_points.d = path.d
        #         stops_points.dd = path.dd
        #         path_list.append(
        #             stops_points)  # path_list is now a couple of Path instances, plus the metadata id,d,dd fields
        #     route_stop_list.append(path_list)
        # return route_stop_list[0]  # transpose a single copy since the others are all repeats (can be verified by path ids)


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

    @timeit
    def __init__(self, system_map, route, stop, period):

        # apply passed parameters to instance
        self.source = 'nj'
        self.route = route
        self.stop = stop
        self.period = period

        # constants
        self.bunching_interval = datetime.timedelta(minutes=3)
        self.bigbang = datetime.timedelta(seconds=0)
        self.stop_name =self.get_stop_name()

        # populate data for webpage
        # self.arrivals_list_final_df, self.stop_name = self.get_arrivals()
        self.arrivals_list_final_df, self.stop_name = self.get_arrivals(self.route,self.stop,self.period)
        self.hourly_frequency = self.get_hourly_frequency()

    def get_stop_name(self): # todo 0 fetch this from system_map using a function

            return 'Stop name TK'

    def get_arrivals_new(self): #todo 0 debug get_arrivals_new using__query_factory inherited from parent class
        with SQLAlchemyDBConnection() as db:

            # build query and load into df
            query=db.session.query(Trip.rt, # base query
                                        Trip.v,
                                        Trip.pid,
                                        Trip.trip_id,
                                        ScheduledStop.trip_id,
                                        ScheduledStop.stop_id,
                                        ScheduledStop.stop_name,
                                        ScheduledStop.arrival_timestamp) \
                                        .join(ScheduledStop) \
                                        .filter(Trip.rt == self.route) \
                                        .filter(ScheduledStop.stop_id == self.stop) \
                                        .filter(ScheduledStop.arrival_timestamp != None)

            query=self.query_factory(db, query,period=self.period) # add the period
            query=query.statement
            try:
                arrivals_here=pd.read_sql(query, db.session.bind)
            except ValueError:
                pass

            # if the database didn't have results, return an empty dataframe
            if len(arrivals_here.index) == 0:
                arrivals_list_final_df = pd.DataFrame(
                    columns=['rt', 'v', 'pid', 'trip_trip_id', 'stop_trip_id', 'stop_name', 'arrival_timestamp'],
                    data=['0', '0000', '0', '0000_000_00000000', '0000_000_00000000', 'N/A', datetime.time(0, 1)]
                )
                stop_name = 'N/A'

                self.arrivals_table_time_created = datetime.datetime.now() # log creation time and return

                return arrivals_list_final_df, stop_name

            else:

                # Otherwise, cleanup the query results -- split by vehicle and calculate arrival intervals

                    # alex r says:
                    # for group in df['col'].unique():
                    #     slice = df[df['col'] == group]
                    #
                    # is like 10x faster than
                    # df.groupby('col').apply( < stuffhere >)

                final_approach_dfs = [g for i, g in arrivals_here.groupby(arrivals_here['v'].ne(arrivals_here[
                                                                                                    'v'].shift()).cumsum())]  # split final approach history (sorted by timestamp) at each change in vehicle_id outputs a list of dfs per https://stackoverflow.com/questions/41144231/python-how-to-split-pandas-dataframe-into-subsets-based-on-the-value-in-the-fir
                arrivals_list_final_df = pd.DataFrame()  # take the last V(ehicle) approach in each df and add it to final list of arrivals
                for final_approach in final_approach_dfs:  # iterate over every final approach
                    arrival_insert_df = final_approach.tail(1)  # take the last observation
                    arrivals_list_final_df = arrivals_list_final_df.append(arrival_insert_df)  # insert into df
                arrivals_list_final_df['delta'] = (
                            arrivals_list_final_df['arrival_timestamp'] - arrivals_list_final_df['arrival_timestamp'].shift(
                        1)).fillna(0)  # calc interval between last bus for each row, fill NaNs

                stop_name = arrivals_list_final_df['stop_name'].iloc[0]

                self.arrivals_table_time_created = datetime.datetime.now() # log creation time and return

                return arrivals_list_final_df, stop_name



    # fetch arrivals into a df
    def get_arrivals(self,route,stop,period):

        with SQLAlchemyDBConnection() as db:
            today_date = datetime.date.today()
            yesterday = datetime.date.today() - datetime.timedelta(1)
            one_hour_ago = datetime.datetime.now() - datetime.timedelta(hours=1)

            if period == "now":
                arrivals_here = pd.read_sql(
                                db.session.query(
                                     Trip.rt,
                                     Trip.v,
                                     Trip.pid,
                                     ScheduledStop.trip_id,
                                     ScheduledStop.stop_id,
                                     ScheduledStop.stop_name,
                                     ScheduledStop.arrival_timestamp)
                                .join(ScheduledStop)
                                .filter(Trip.rt == route)
                                .filter(ScheduledStop.stop_id == stop)
                                .filter(ScheduledStop.arrival_timestamp != None)
                                .filter(func.date(ScheduledStop.arrival_timestamp) > one_hour_ago)
                                .statement
                                ,db.session.bind)


            elif period == "today":
                arrivals_here = pd.read_sql(
                                db.session.query(
                                     Trip.rt,
                                     Trip.v,
                                     Trip.pid,
                                     ScheduledStop.trip_id,
                                     ScheduledStop.stop_id,
                                     ScheduledStop.stop_name,
                                     ScheduledStop.arrival_timestamp)
                                .join(ScheduledStop)
                                .filter(Trip.rt == route)
                                .filter(ScheduledStop.stop_id == stop)
                                .filter(ScheduledStop.arrival_timestamp != None)
                                .filter(func.date(ScheduledStop.arrival_timestamp) == today_date)
                                .statement
                                ,db.session.bind)


            elif period == "yesterday":
                arrivals_here = pd.read_sql(
                                db.session.query(
                                    Trip.rt,
                                    Trip.v,
                                    Trip.pid,
                                    Trip.trip_id,
                                    ScheduledStop.trip_id,
                                    ScheduledStop.stop_id,
                                    ScheduledStop.stop_name,
                                    ScheduledStop.arrival_timestamp)
                                .join(ScheduledStop)
                                .filter(Trip.rt == route)
                                .filter(ScheduledStop.stop_id == stop)
                                .filter(ScheduledStop.arrival_timestamp != None)
                                .filter(func.date(ScheduledStop.arrival_timestamp) == yesterday)
                                .statement
                                 ,db.session.bind)

            elif period == "history":
                arrivals_here = pd.read_sql(
                                db.session.query(
                                    Trip.rt,
                                    Trip.v,
                                    Trip.pid,
                                    Trip.trip_id,
                                    ScheduledStop.trip_id,
                                    ScheduledStop.stop_id,
                                    ScheduledStop.stop_name,
                                    ScheduledStop.arrival_timestamp)
                                .join(ScheduledStop)
                                .filter(Trip.rt == route)
                                .filter(ScheduledStop.stop_id == stop)
                                .filter(ScheduledStop.arrival_timestamp != None)
                                .statement
                                ,db.session.bind)

            elif period is True:
                try:
                    int(period)  # check if it digits (e.g. period=20180810)
                    request_date = datetime.datetime.strptime(period, '%Y%m%d')  # make a datetime object
                    arrivals_here = pd.read_sql(
                                db.session.query(
                                    Trip.rt,
                                    Trip.v,
                                    Trip.pid,
                                    Trip.trip_id,
                                    ScheduledStop.trip_id,
                                    ScheduledStop.stop_id,
                                    ScheduledStop.stop_name,
                                    ScheduledStop.arrival_timestamp)
                                .join(ScheduledStop)
                                .filter(Trip.rt == route)
                                .filter(ScheduledStop.stop_id == stop)
                                .filter(ScheduledStop.arrival_timestamp != None)
                                .filter(func.date(ScheduledStop.arrival_timestamp) == request_date)
                                .statement
                                , db.session.bind)

                except ValueError:
                        pass

            # if the database didn't have results, return an empty dataframe
            if len(arrivals_here.index) == 0:

                arrivals_list_final_df = pd.DataFrame(
                    columns=['rt', 'v', 'pid', 'trip_trip_id', 'stop_trip_id', 'stop_name', 'arrival_timestamp'],
                    data=['0', '0000', '0', '0000_000_00000000', '0000_000_00000000', 'N/A', datetime.time(0, 1)]
                    )
                stop_name = 'N/A'
                self.arrivals_table_time_created = datetime.datetime.now()

                return arrivals_list_final_df, stop_name

            # Otherwise, cleanup the query results
            # split by vehicle and calculate arrival intervals

            # todo 0 optimize the groupby here
            # alex r says:
            # for group in df['col'].unique():
            #     slice = df[df['col'] == group]
            #
            # is like 10x faster than
            # df.groupby('col').apply( < stuffhere >)


            final_approach_dfs = [g for i, g in arrivals_here.groupby(arrivals_here['v'].ne(arrivals_here['v'].shift()).cumsum())] # split final approach history (sorted by timestamp) at each change in vehicle_id outputs a list of dfs per https://stackoverflow.com/questions/41144231/python-how-to-split-pandas-dataframe-into-subsets-based-on-the-value-in-the-fir
            arrivals_list_final_df = pd.DataFrame() # take the last V(ehicle) approach in each df and add it to final list of arrivals
            for final_approach in final_approach_dfs:  # iterate over every final approach
                arrival_insert_df = final_approach.tail(1)  # take the last observation
                arrivals_list_final_df = arrivals_list_final_df.append(arrival_insert_df)  # insert into df
            arrivals_list_final_df['delta']=(arrivals_list_final_df['arrival_timestamp'] - arrivals_list_final_df['arrival_timestamp'].shift(1)).fillna(0) # calc interval between last bus for each row, fill NaNs

            stop_name = arrivals_list_final_df['stop_name'].iloc[0]

            return arrivals_list_final_df, stop_name

    def get_hourly_frequency(self):
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


