# import pickle
import datetime
import sys
# from operator import itemgetter
import pandas as pd
# import geojson, json

from sqlalchemy import inspect, func

import lib.BusAPI as BusAPI
from lib.DataBases import SQLAlchemyDBConnection, Trip, BusPosition, ScheduledStop

from route_config import reportcard_routes, grade_descriptions, city_collections


# helper to retrieve a collection from config

def load_collection_metadata():
    return city_collections


def parse_collection_metadata(collection_url):
    collection_metadata = dict()
    # iterate over collection and grab the one that matches
    for city in city_collections:
        if city['collection_url']==collection_url:
            collection_metadata=city
    return collection_metadata


# primary classes
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
        self.reportcard_routes = reportcard_routes
        self.grade_descriptions = grade_descriptions

        # populate static report card data
        #todo -- would be nice to read this from Trip, but since RouteReport has more than 1 trip, which path will we use? this is why buses sometimes show up on maps not on a route
        self.routename, self.waypoints_coordinates, self.stops_coordinates, self.waypoints_geojson, self.stops_geojson = self.get_route_geojson_and_name(self.route)
        self.load_route_description()
        self.route_stop_list = self.get_stoplist(self.route)

        # populate live report card data
        # self.active_trips = self.get_activetrips() <-- depreceated?
        self.grade, self.grade_description = self.get_grade(period)
        # todo self.headway = self.get_headway()
        self.bunching_badboys = self.get_bunching_badboys(period)
        self.traveltime = self.get_traveltime(period)
        self.get_period_labels = self.get_period_labels()
        self.tripdash = self.get_tripdash()


    # get a list of trips current running the route

    def __get_current_trips(self):

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


    # def __build_period_filter(self,db,object_class):
    #
    #     today_date = datetime.date.today()
    #
    #     if self.period == 'today':
    #         period_filter = db.session.query(object_class)\
    #             .filter(func.date(object_class.arrival_timestamp) == today_date)
    #
    #     return period_filter


    def get_period_labels(self):
        if self.period == 'now':
            period_label = 'Todays'
        else:
            period_label = '-no period label assigned-'
        return period_label


    def get_headway(self):

        with SQLAlchemyDBConnection() as db:

            headway = dict()

            todays_date = datetime.date.today()
            yesterdays_date = datetime.date.today() - datetime.timedelta(1)
            one_hour_ago = datetime.datetime.now() - datetime.timedelta(hours=1)

            x, trips_on_road_now = self.__get_current_trips()

            if self.period == 'now':
                arrivals_in_completed_trips=pd.read_sql(
                    db.session.query( ScheduledStop.trip_id,
                                     ScheduledStop.stop_id,
                                     ScheduledStop.stop_name,
                                     ScheduledStop.arrival_timestamp)
                    .filter(ScheduledStop.arrival_timestamp != None)
                    .filter(func.date(ScheduledStop.arrival_timestamp) > one_hour_ago) # todo last hour
                    .filter(ScheduledStop.trip_id.notin_(trips_on_road_now))
                    .order_by(ScheduledStop.trip_id.asc())
                    .order_by(ScheduledStop.pkey.asc())
                    .statement,
                    db.session.bind)

            elif self.period == 'today':
                arrivals_in_completed_trips=pd.read_sql(
                    db.session.query( ScheduledStop.trip_id,
                                     ScheduledStop.stop_id,
                                     ScheduledStop.stop_name,
                                     ScheduledStop.arrival_timestamp)
                    .filter(ScheduledStop.arrival_timestamp != None)
                    .filter(func.date(ScheduledStop.arrival_timestamp) == todays_date)
                    .filter(ScheduledStop.trip_id.notin_(trips_on_road_now))
                    .order_by(ScheduledStop.trip_id.asc())
                    .order_by(ScheduledStop.pkey.asc())
                    .statement,
                    db.session.bind)


            elif self.period == 'yesterday':
                arrivals_in_completed_trips=pd.read_sql(
                    db.session.query( ScheduledStop.trip_id,
                                     ScheduledStop.stop_id,
                                     ScheduledStop.stop_name,
                                     ScheduledStop.arrival_timestamp)
                    .filter(ScheduledStop.arrival_timestamp != None)
                    .filter(func.date(ScheduledStop.arrival_timestamp) == yesterdays_date)
                    .filter(ScheduledStop.trip_id.notin_(trips_on_road_now))
                    .order_by(ScheduledStop.trip_id.asc())
                    .order_by(ScheduledStop.pkey.asc())
                    .statement,
                    db.session.bind)

            elif self.period == 'history':
                arrivals_in_completed_trips=pd.read_sql(
                    db.session.query( ScheduledStop.trip_id,
                                     ScheduledStop.stop_id,
                                     ScheduledStop.stop_name,
                                     ScheduledStop.arrival_timestamp)
                    .filter(ScheduledStop.arrival_timestamp != None)
                    .filter(ScheduledStop.trip_id.notin_(trips_on_road_now))
                    .order_by(ScheduledStop.trip_id.asc())
                    .order_by(ScheduledStop.pkey.asc())
                    .statement,
                    db.session.bind)


            # if the database didn't have results, return an empty dataframe
            if len(arrivals_in_completed_trips.index) == 0:
                arrivals_in_completed_trips = pd.DataFrame(
                    columns=['trip_id', 'stop_id', 'stop_name', 'arrival_timestamp'],
                    data=[['0000_000_00000000', '0000_000_00000000', 'N/A', datetime.datetime(2010,1,1,7,0,0)]]
                    )

            # Otherwise, split by stop_id and calculate arrival intervals at each stop
            stop_dfs = [g for i, g in arrivals_in_completed_trips.groupby(arrivals_in_completed_trips['stop_id'].ne(arrivals_in_completed_trips['stop_id'].shift()).cumsum())]
            headways_df = pd.DataFrame()
            for stop_df in stop_dfs:  # iterate over every stop
                stop_df['delta'] = (stop_df['arrival_timestamp'] - stop_df['arrival_timestamp'].shift(1)).fillna(0) # calc interval between last bus for each row, fill NaNs
                stop_df=stop_df.dropna() # drop the NaN (probably just the first one)
                headways_df = headways_df.append(stop_df)  # dump all these rows into the headways list

            # average headway for route -- entire period
            headway['period_mean'] = headways_df['delta'].mean()
            headway['period_std'] = headways_df['delta'].std()

            # average headway for route -- by hour
            times = pd.DatetimeIndex(headways_df.arrival_timestamp)
            hourly_arrival_groups = headways_df.groupby([times.hour, times.minute])
            headway['hourly_mean'] = list()
            headway['hourly_std'] = list()

            for hourly_arrivals in hourly_arrival_groups:

                df_hourly_arrivals=hourly_arrivals[1] # grab the df from the tuple
                # append the summary statistics to the headway dict
                headway['hourly_mean'].append((df_hourly_arrivals['arrival_timestamp'].hour, df_hourly_arrivals.mean()))
                headway['hourly_std'].append((df_hourly_arrivals['arrival_timestamp'].hour, df_hourly_arrivals.std()))


                # # iterate over the df to compute the means and stds
                # for index, row in df_hourly_arrivals.iterrows():
                #     print row['c1'], row['c2']



            # default for testing template

            headway['time'] = 20
            headway['description'] = 'pretty good'

            return headway


    def get_bunching_badboys(self,period):
        bunching_badboys = dict()
        bunching_badboys['flag'] = True
        bunching_badboys['label'] = 'a lot'
        bunching_badboys['stops']=list()
        bunching_badboys['stops'].append('Central Ave + Beacon Ave')
        bunching_badboys['stops'].append('Martin Luther King Jr Dr + Bidwell Ave')
        bunching_badboys['stops'].append('Palisade Ave + Hutton St')
        #
        # # todo check if bunching leaderboard is current
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
        #         for stop in service.stops: #todo first query to make sure there are ScheduledStop instances
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



    def get_grade(self, period):

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
        # todo read from self.grade_descriptions
        grade_description = 'Service meets the needs of riders some of the time, but suffers from serious shortcomings and gaps. Focused action is required to improve service in the near-term.'
        return grade, grade_description




    def get_traveltime(self, period):
        traveltime = dict()
        traveltime['headline'] = 'good'
        traveltime['time'] = 20
        traveltime['percent'] = 13
        traveltime['label'] = 'below'

        # algorithm v/simple
        #
        # for all observed trips over the `{period}`
        #   sort all scheduledstops by arrival_time
        #   compute elapsed time from earliest observation (arrival at first stop) to last observaton (arrival at last stop)
        # take the mean of these

        return traveltime

    def get_route_geojson_and_name(self, route):
        routes, coordinate_bundle = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data(self.source, 'routes', route=route))
        return routes[0].nm, coordinate_bundle['waypoints_coordinates'], coordinate_bundle['stops_coordinates'], coordinate_bundle['waypoints_geojson'], coordinate_bundle['stops_geojson']

    def load_route_description(self):
        for route in self.reportcard_routes:
            if route['route'] == self.route:
                self.frequency = route['frequency']
                self.description_long = route['description_long']
                self.prettyname = route['prettyname']
                self.schedule_url = route['schedule_url']
            else:
                pass
        return

    # gets all stops on all active routes
    def get_stoplist(self, route):
        routes, coordinate_bundle = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data(self.source, 'routes', route=self.route))
        route_stop_list = []
        for r in routes:
            path_list = []
            for path in r.paths:
                stops_points = RouteReport.Path()
                for point in path.points:
                    if isinstance(point, BusAPI.Route.Stop):
                        stops_points.stops.append(point)
                stops_points.id=path.id
                stops_points.d=path.d
                stops_points.dd=path.dd
                path_list.append(stops_points) # path_list is now a couple of Path instances, plus the metadata id,d,dd fields
            route_stop_list.append(path_list)
        return route_stop_list[0] # transpose a single copy since the others are all repeats (can be verified by path ids)

    # gets all arrivals (see limit) for all runs on current route
    def get_tripdash(self):
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

        # self.citywide_waypoints_geojson = get_systemwide_geojson(reportcard_routes)
        # self.stop_lnglatlike, self.stop_geojson = self.get_stop_lnglatlike()

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

