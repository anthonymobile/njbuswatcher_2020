import datetime
import pandas as pd
import numpy as np
# import geojson, json

from sqlalchemy import func
from sqlalchemy.orm import Query
# from sqlalchemy import inspect

import buswatcher.lib.BusAPI as BusAPI
import buswatcher.lib.RouteConfig as RouteConfig

from buswatcher.lib.DataBases import SQLAlchemyDBConnection, Trip, BusPosition, ScheduledStop

# primary classes


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
        self.headway = self.get_headway()
        self.bunching_badboys = self.get_bunching_badboys(period)
        self.grade, self.grade_description = self.get_grade(period)
        self.traveltime = self.get_traveltime(period)

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


    def get_headway(self):

        with SQLAlchemyDBConnection() as db:

            # build the query
            x, trips_on_road_now = self.__get_current_trips()

            query = db.session.query(ScheduledStop).\
                        add_columns(ScheduledStop.trip_id,
                            ScheduledStop.stop_id,
                            ScheduledStop.stop_name,
                            ScheduledStop.arrival_timestamp)

            # example of multi-table query -- would it require re-setting the relationships in DataBases.py class definitions?
            # # query = df.session.query(Trip, ScheduledStop, BusPosition).join(ScheduledStop).join(BusPosition)

            # add the period
            query = self.__query_factory(db, query, period=self.period) # todo fix __query factory -- look at other bigdate filters like wwwAPI.get_traveltime -- for some reason the date filters aren't working (e.g. > :date_1)

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
            arrivals_in_completed_trips = pd.read_sql(query,db.session.bind)
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
            stop_dfs = [g for i, g in arrivals_in_completed_trips.groupby(arrivals_in_completed_trips['stop_id'].ne(arrivals_in_completed_trips['stop_id'].shift()).cumsum())]
            headways_df = pd.DataFrame()
            for stop_df in stop_dfs:  # iterate over every stop
                stop_df['delta'] = (stop_df['arrival_timestamp'] - stop_df['arrival_timestamp'].shift(1)).fillna(0) # calc interval between last bus for each row, fill NaNs
                stop_df=stop_df.dropna() # drop the NaN (probably just the first one)
                headways_df = headways_df.append(stop_df)  # dump all these rows into the headways list

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

                df_hourly_arrivals=hourly_arrivals[1] # grab the df from the tuple
                hour = datetime.time(7) #todo 1 make dynamic with the actual hour

                # try this https://stackoverflow.com/questions/45239742/aggregations-for-timedelta-values-in-the-python-dataframe
                mean = df_hourly_arrivals.delta.mean(numeric_only=False)
                std = df_hourly_arrivals.delta.std(numeric_only=False)

                # compute the summary stats using numpy per https://stackoverflow.com/questions/44616546/finding-the-mean-and-standard-deviation-of-a-timedelta-object-in-pandas-df
                # mean2 = df_hourly_arrivals.delta.apply(lambda x: np.mean(x))
                # std2 = df_hourly_arrivals.delta.apply(lambda x: np.std(x))

                headway['hourly_table'].append((hour,mean,std))

            # todo 2 average headway -- by hour, by stop

            return headway

    def get_traveltime(self, period):  # todo 1 write and test get_traveltime using new query_factory

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
            # if self.period == 'now':
            #     arrivals_in_completed_trips = pd.read_sql(
            #         db.session.query(ScheduledStop.trip_id,
            #                          ScheduledStop.stop_id,
            #                          ScheduledStop.stop_name,
            #                          ScheduledStop.arrival_timestamp)
            #             .filter(ScheduledStop.arrival_timestamp != None)
            #             # todo 0 last hour doesnt work
            #             .filter(func.date(ScheduledStop.arrival_timestamp) > one_hour_ago)
            #             .filter(ScheduledStop.trip_id.notin_(trips_on_road_now))
            #             .order_by(ScheduledStop.trip_id.asc())
            #             .order_by(ScheduledStop.arrival_timestamp.asc())
            #             .statement,
            #         db.session.bind)
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
            # elif self.period == 'yesterday':
            #     arrivals_in_completed_trips = pd.read_sql(
            #         db.session.query(ScheduledStop.trip_id,
            #                          ScheduledStop.stop_id,
            #                          ScheduledStop.stop_name,
            #                          ScheduledStop.arrival_timestamp)
            #             .filter(ScheduledStop.arrival_timestamp != None)
            #             .filter(func.date(ScheduledStop.arrival_timestamp) == yesterdays_date)
            #             .filter(ScheduledStop.trip_id.notin_(trips_on_road_now))
            #             .order_by(ScheduledStop.trip_id.asc())
            #             .order_by(ScheduledStop.arrival_timestamp.asc())
            #             .statement,
            #         db.session.bind)
            #
            # elif self.period == 'history':
            #     arrivals_in_completed_trips = pd.read_sql(
            #         db.session.query(ScheduledStop.trip_id,
            #                          ScheduledStop.stop_id,
            #                          ScheduledStop.stop_name,
            #                          ScheduledStop.arrival_timestamp)
            #             .filter(ScheduledStop.arrival_timestamp != None)
            #             .filter(ScheduledStop.trip_id.notin_(trips_on_road_now))
            #             .order_by(ScheduledStop.trip_id.asc())
            #             .order_by(ScheduledStop.arrival_timestamp.asc())
            #             .statement,
            #         db.session.bind)
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

    def get_bunching_badboys(self,period): # todo 1 finish route bunching metric

        bunching_badboys = dict()
        bunching_badboys['flag'] = True
        bunching_badboys['label'] = 'a lot'
        bunching_badboys['stops']=list()
        bunching_badboys['stops'].append('Central Ave + Beacon Ave')
        bunching_badboys['stops'].append('Martin Luther King Jr Dr + Bidwell Ave')
        bunching_badboys['stops'].append('Palisade Ave + Hutton St')
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

        return bunching_badboys

    def get_grade(self, period): # todo 1 finish route grade metric

        # based on A. average headway standard deviation

        # We can also report variability using standard deviation and that can be converted to a letter
        # (e.g.A is < 1 s.d., B is 1 to 1.5, etc.)
        # Example: For a headway of 20 minutes, a service dependability grade of B means 80 percent of the time the bus will come every 10 to 30 minutes.
        # for each (completed trip) in (period)
        #   for each (stop) on (trip)
        #       if period = now
        #           what is the average time between the last 2-3 arrivals
        #       elif period = anything else
        #           what is the average time between all the arrivals in the period

        # and B. number of bunching incidents
        grade = 'B'
        # todo 1 read from self.grade_descriptions
        grade_description = 'Service meets the needs of riders some of the time, but suffers from serious shortcomings and gaps. Focused action is required to improve service in the near-term.'
        return grade, grade_description

    def get_tripdash(self): # gets all arrivals (see limit) for all runs on current route

        with SQLAlchemyDBConnection() as db:

            # # build a list of tuples with (run, trip_id)
            # v_on_route = BusAPI.parse_xml_getBusesForRoute(BusAPI.get_xml_data(self.source, 'buses_for_route', route=self.route))
            # todays_date = datetime.datetime.today().strftime('%Y%m%d')
            # trip_list=list()
            #
            # for v in v_on_route:
            #     trip_id=('{a}_{b}_{c}').format(a=v.id,b=v.run, c=todays_date)
            #     trip_list.append((trip_id, v.pd, v.bid, v.run))
            #

            trip_list, x = self.__get_current_trips()

            tripdash = dict()
            for trip_id,pd,bid,run in trip_list:

                # load the trip card - full with all the missed stops
                # scheduled_stops = db.session.query(ScheduledStop) \
                #     .join(Trip) \
                #     .filter(Trip.trip_id == trip_id) \
                #     .order_by(ScheduledStop.pkey.asc()) \
                #     .all()

                # load the trip card - pretty
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

    # todo 1 write stop get_arrivals arrivals dashboard
    # todo 1 write stop get_frequency_report
    # to do 2 write stop get_travel_time metric
    # to do 2 write stop get_grade metric
