import datetime
import pandas as pd

from sqlalchemy import func

import buswatcher.lib.BusAPI as BusAPI
import buswatcher.lib.RouteConfig as RouteConfig
from buswatcher.lib.DataBases import SQLAlchemyDBConnection, Trip, BusPosition, ScheduledStop


class NJTransitSystem:

    def __init__(self):

        # load the basics
        self.route_definitions, self.grade_descriptions, self.collection_descriptions = RouteConfig.load_config()

        # load the route table
        self.route_geometries = [({'route':r['route'],'xml':RouteConfig.get_route_geometry(r['route'])}) for r in self.route_definitions['route_definitions']]


class RouteReport:

    class Path():
        def __init__(self):
            self.name = 'Path'
            self.stops = []
            self.id = ''
            self.d = ''
            self.dd = ''

    def __init__(self, source, route, period):

        # apply passed parameters to instance
        self.source = source
        self.route = route
        self.period = period

        # populate route basics from config

        self.route_definitions, self.grade_descriptions, self.collection_descriptions = RouteConfig.load_config()

        # populate static report card data
        self.__load_route_description()
        self.route_geometry = RouteConfig.get_route_geometry(route)
        self.routes, self.coordinate_bundle = BusAPI.parse_xml_getRoutePoints(RouteConfig.get_route_geometry(self.route))
        self.routename, self.waypoints_coordinates, self.stops_coordinates, self.waypoints_geojson, self.stops_geojson = self.routes[0].nm, self.coordinate_bundle['waypoints_coordinates'], self.coordinate_bundle['stops_coordinates'], self.coordinate_bundle['waypoints_geojson'], self.coordinate_bundle['stops_geojson']
        self.route_stop_list = self.__get_stoplist()
        self.period_labels = self.__get_period_labels()

        # populate live report card data
        self.bunching_badboys = self.get_bunching_badboys()
        # self.bunching_badboys = generator.fetch_bunching_report(RouteReport)
        self.grade, self.grade_description = self.get_grade()

        # FUTURE
        # self.headway = self.get_headway()
        # self.traveltime = self.get_traveltime(period)

        self.tripdash = self.get_tripdash()

    def __load_route_description(self):
        for route in self.route_definitions['route_definitions']:
            if route['route'] == self.route:
                self.frequency = route['frequency']
                self.description_long = route['description_long']
                self.prettyname = route['prettyname']
                self.schedule_url = route['schedule_url']
            else:
                pass
        return

    def __get_period_labels(self):
        if self.period == 'now':
            period_label = "current"
        elif self.period == 'today':
            period_label = "today's"
        elif self.period == 'yesterday':
            period_label = "yesterday's"
        elif self.period == 'history':
            period_label = "forever's"
        else:
            period_label = '-no period label assigned-'
        return period_label

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

    def __get_stoplist(self):
        routes, coordinate_bundle = BusAPI.parse_xml_getRoutePoints(self.route_geometry)
        # routes, coordinate_bundle = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data(self.source, 'routes', route=self.route))
        route_stop_list = []
        for r in routes:
            path_list = []
            for path in r.paths:
                stops_points = RouteReport.Path()
                for point in path.points:
                    if isinstance(point, BusAPI.Route.Stop):
                        stops_points.stops.append(point)
                stops_points.id = path.id
                stops_points.d = path.d
                stops_points.dd = path.dd
                path_list.append(
                    stops_points)  # path_list is now a couple of Path instances, plus the metadata id,d,dd fields
            route_stop_list.append(path_list)
        return route_stop_list[0]  # transpose a single copy since the others are all repeats (can be verified by path ids)

    def __query_factory(self, db, query, **kwargs):


        # todo 0 possible solution https://stackoverflow.com/questions/7075828/make-sqlalchemy-use-date-in-filter-using-postgresql

        # my_data = session.query(MyObject). \
        #    filter(cast(MyObject.date_time, Date) == date.today()).all()


        todays_date = datetime.date.today()
        yesterdays_date = datetime.date.today() - datetime.timedelta(1)
        one_hour_ago = datetime.datetime.now() - datetime.timedelta(hours=1)

        # todo 0 working on this period to find a solution
        if kwargs['period'] == 'now':
            # query = query.filter(ScheduledStop.arrival_timestamp != None).filter(func.date(ScheduledStop.arrival_timestamp) > one_hour_ago) # todo 2 fix one_hour_ago period query filter. right now we just use same as 'today'
            query = query.filter(ScheduledStop.arrival_timestamp != None).filter(func.date(ScheduledStop.arrival_timestamp) == todays_date)
        elif kwargs['period'] == 'today':
            query = query.filter(ScheduledStop.arrival_timestamp != None).filter(func.date(ScheduledStop.arrival_timestamp) == todays_date)
        elif kwargs['period'] == 'yesterday':
            query = query.filter(ScheduledStop.arrival_timestamp != None).filter(func.date(ScheduledStop.arrival_timestamp) == yesterdays_date)
        elif kwargs['period'] == 'history':
            query = query.filter(ScheduledStop.arrival_timestamp != None)

        return query

    def get_tripdash(self): # gets all arrivals (see limit) for all runs on current route

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

                # load the trip card - limit 5
                scheduled_stops = db.session.query(ScheduledStop) \
                    .join(Trip) \
                    .filter(Trip.trip_id == trip_id) \
                    .filter(ScheduledStop.arrival_timestamp != None) \
                    .order_by(ScheduledStop.pkey.desc()) \
                    .limit(5) \
                    .all()

                trip_dict=dict()
                trip_dict['stoplist']=scheduled_stops
                trip_dict['pd'] = pd
                trip_dict['v'] = bid
                trip_dict['run'] = run
                tripdash[trip_id] = trip_dict

        return tripdash

    def get_bunching_badboys(self):

        bunching_badboys = dict()
        bunching_badboys['flag'] = True
        bunching_badboys['label'] = 'a lot'
        bunching_badboys['stops']=list()
        bunching_badboys['stops'].append('Central Ave + Beacon Ave')
        bunching_badboys['stops'].append('Martin Luther King Jr Dr + Bidwell Ave')
        bunching_badboys['stops'].append('Palisade Ave + Hutton St')

        return bunching_badboys

    def get_grade(self): # todo 1 finish route grade metric

        # todo 0 -- based on # of bunching incidents
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

        grade = 'B'
        grade_description = "This isn't working."
        return grade, grade_description

        # FUTURE -- based on average headway standard deviation

        # We can also report variability using standard deviation and that can be converted to a letter
        # (e.g.A is < 1 s.d., B is 1 to 1.5, etc.)
        # Example: For a headway of 20 minutes, a service dependability grade of B means 80 percent of the time the bus will come every 10 to 30 minutes.
        # for each (completed trip) in (period)
        #   for each (stop) on (trip)
        #       if period = now
        #           what is the average time between the last 2-3 arrivals
        #       elif period = anything else
        #           what is the average time between all the arrivals in the period

    # def get_headway(self):
    #     return
    #
    # def get_traveltime(self):
    #     return

class StopReport:

    def __init__(self, source, route, stop, period):
        # apply passed parameters to instance
        self.source = source
        self.route = route
        self.stop = stop
        self.period = period

        # constants
        self.bunching_interval = datetime.timedelta(minutes=3)
        self.bigbang = datetime.timedelta(seconds=0)

        # populate data for webpage
        self.arrivals_list_final_df, self.stop_name = self.get_arrivals(self.route, self.stop, self.period)
        self.hourly_frequency = self.get_hourly_frequency()

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


