import pickle
import datetime
import pandas as pd
import geojson

from sqlalchemy import inspect, func

import lib.BusAPI as BusAPI
from lib.DataBases import DBConfig, SQLAlchemyDBConnection, Trip, BusPosition, ScheduledStop

from route_config import reportcard_routes, grade_descriptions

# common functions
def timestamp_fix(data,key): # trim the microseconds off the timestamp and convert it to datetime format
    data[key] = data[key].str.split('.').str.get(0)
    data[key] = pd.to_datetime(data[key],errors='coerce')
    # data = data.set_index(pd.DatetimeIndex(data['timestamp']))
    data = data.set_index(pd.DatetimeIndex(data[key]), drop=False)
    return data

# convery sqlalchemy query to a dict
# https://stackoverflow.com/questions/1958219/convert-sqlalchemy-row-object-to-python-dict
def object_as_dict(obj):
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}

# geoJSON for citywide map
def citymap_geojson(reportcard_routes):
    points = []
    stops = []
    for i in reportcard_routes:
        routes, coordinate_bundle = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data('nj', 'routes', route=i['route']))
        points_feature = coordinate_bundle['waypoints_geojson']
        stops_feature = coordinate_bundle['stops_geojson']

        points.append(points_feature)
        stops.append(stops_feature)
    map_points = geojson.FeatureCollection(points)
    map_stops = geojson.FeatureCollection(stops)
    return map_points, map_stops


# primary classes
class RouteReport:

    class Path():
        def __init__(self):
            self.name = 'Path'
            self.stops = []
            self.id = ''
            self.d = ''
            self.dd = ''

    def __init__(self, source, route):

        # apply passed parameters to instance
        self.source = source
        self.route = route

        # populate route basics from config
        self.reportcard_routes = reportcard_routes
        self.grade_descriptions = grade_descriptions

        # populate static report card data
        self.routename, self.waypoints_coordinates, self.stops_coordinates, self.waypoints_geojson, self.stops_geojson = self.get_routename(self.route) #todo -- can we eliminate this? redundant -- read it from Trip?
        self.load_route_description()
        self.route_stop_list = self.get_stoplist(self.route)

        # populate live report card data
        self.active_trips = self.get_activetrips()


    def get_routename(self,route):
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


    def get_activetrips(self):

        # query db and load up everything we want to display
        # (basically what's on the approach_dash)

        active_trips = list()

        todays_date = datetime.datetime.today().strftime('%Y%m%d')

        # grab buses on road now and populate trip cards
        buses_on_route = BusAPI.parse_xml_getBusesForRoute(BusAPI.get_xml_data(self.source, 'buses_for_route', route=self.route))
        for b in buses_on_route:
            current_trip = dict()
            trip_id = ('{id}_{run}_{dt}').format(id=b.id, run=b.run, dt=datetime.datetime.today().strftime('%Y%m%d'))

            with SQLAlchemyDBConnection(DBConfig.conn_str) as db:
                # load the trip card, dropping anything without an arrival
                scheduled_stops = db.session.query(Trip.pid, Trip.trip_id, ScheduledStop.trip_id, ScheduledStop.stop_id, ScheduledStop.stop_name, ScheduledStop.arrival_timestamp) \
                    .join(ScheduledStop) \
                    .filter(Trip.trip_id == trip_id) \
                    .filter(ScheduledStop.arrival_timestamp != None) \
                    .all()
                    #todo sort on something?

                #convert the query
                # active trips is a list, each item contains a dict
                # {'pid': 1634, 'trip_id': '5722_16_20190208', 'stop_id': 20496, 'arrival_timestamp': None}
                current_trip['trip_id'] = trip_id
                current_trip['trip_card'] = list(map(lambda obj: dict(zip(obj.keys(), obj)), scheduled_stops))
                active_trips.append(current_trip)

        # reverse sort on timestamp then take the first 5 and return both
        # https://www.w3resource.com/python-exercises/list/python-data-type-list-exercise-50.php
        for trip in active_trips:
            trip['trip_card'].sort(key=lambda x: x['arrival_timestamp'], reverse=True)
            trip['trip_card']=trip['trip_card'][:5]

        # active_trips_5=active_trips[:5] # todo this is clipping the wrong thing -- limiting to 5 trips, not 5 arrivals per trip

        return active_trips

    ###########################################################
    # functions to work on
    ###########################################################

    # def get_tripdash(self, ++? source, route, run):
    #
    #     with SQLAlchemyDBConnection(DBConfig.conn_str) as db:
    #
    #         # compute trip_ids
    #         todays_date = datetime.datetime.today().strftime('%Y%m%d')
    #         trip_id_list = []
    #         v_on_route = BusAPI.parse_xml_getBusesForRoute(BusAPI.get_xml_data(source, 'buses_for_route', route=route))
    #         for v in v_on_route:
    #             if v.run == run:
    #                 trip_id = (('{a}_{b}_{c}').format(a=v.id, b=v.run, c=todays_date))
    #             else:
    #                 pass
    #         trips_dash = dict()
    #         # load the trip card
    #         scheduled_stops = db.session.query(ScheduledStop) \
    #             .join(Trip) \
    #             .filter(Trip.trip_id == trip_id) \
    #             .order_by(ScheduledStop.pkey.asc()) \
    #             .all()
    #         trips_dash[trip_id] = scheduled_stops
    #
    #     return trips_dash

    # pull this from the database based on the Tripid?
    # using with SQLAlchemyDBConnection as db:
    # def generate_bunching_leaderboard(self, period, route):
    #     # generates top 10 list of stops on the route by # of bunching incidents for period
    #     bunching_leaderboard = []
    #     cum_arrival_total = 0
    #     cum_bunch_total = 0
    #     for service in self.route_stop_list:
    #         for stop in service.stops:
    #             bunch_total = 0
    #             arrival_total = 0
    #             report = StopReport(self.route, stop.identity,period)
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
    #     # compute grade passed on pct of all stops on route during period that were bunched
    #     try:
    #         grade_numeric = (cum_bunch_total / cum_arrival_total) * 100
    #         for g in self.grade_descriptions:
    #             if g['bounds'][0] < grade_numeric <= g['bounds'][1]:
    #                 self.grade = g['grade']
    #                 self.grade_description = g['description']
    #     except:
    #         self.grade = 'N/A'
    #         self.grade_description = 'Unable to determine grade.'
    #         pass
    #
    #     time_created = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    #     bunching_leaderboard_pickle = dict(bunching_leaderboard=bunching_leaderboard, grade=self.grade,
    #                                        grade_numeric=grade_numeric, grade_description=self.grade_description, time_created=time_created)
    #     outfile = ('data/bunching_leaderboard_'+route+'.pickle')
    #     with open(outfile, 'wb') as handle:
    #         pickle.dump(bunching_leaderboard_pickle, handle, protocol=pickle.HIGHEST_PROTOCOL)
    #     return


    # def load_bunching_leaderboard(self,route):
    #     infile = ('data/bunching_leaderboard_'+route+'.pickle')
    #     with open(infile, 'rb') as handle:
    #         b = pickle.load(handle)
    #     return b['bunching_leaderboard'], b['grade'], b['grade_numeric'], b['grade_description'], b['time_created']



class StopReport:

    def __init__(self, route, stop, period):
        # apply passed parameters to instance
        self.route = route
        self.stop = stop
        self.period = period

        # populate stop report data
        self.arrivals_list_final_df, self.stop_name = self.get_arrivals(self.route, self.stop, self.period)

        # constants
        self.bunching_interval = datetime.timedelta(minutes=3)
        self.bigbang = datetime.timedelta(seconds=0)

    # fetch arrivals into a df
    def get_arrivals(self,route,stop,period):

        try:
            with SQLAlchemyDBConnection(DBConfig.conn_str) as db:
                today_date = datetime.date.today()
                yesterday = datetime.date.today() - datetime.timedelta(1)

                if period == "daily":
                    arrivals_here = pd.read_sql(db.session.query(Trip.v, Trip.trip_id, Trip.pid, Trip.trip_id,
                                                                 ScheduledStop.trip_id, ScheduledStop.stop_id,
                                                                 ScheduledStop.stop_name, ScheduledStop.arrival_timestamp)
                                                    .join(ScheduledStop)
                                                    .filter(ScheduledStop.stop_id == stop)
                                                    .filter(ScheduledStop.arrival_timestamp != None)
                                                    .filter(func.date(ScheduledStop.arrival_timestamp) == today_date)
                                                     .statement
                                                    ,db.session.bind)

                elif period == "yesterday":
                    arrivals_here = pd.read_sql(db.session.query(Trip.v, Trip.trip_id, Trip.pid, Trip.trip_id,
                                                                 ScheduledStop.trip_id, ScheduledStop.stop_id,
                                                                 ScheduledStop.stop_name, ScheduledStop.arrival_timestamp)
                                                    .join(ScheduledStop)
                                                    .filter(ScheduledStop.stop_id == stop)
                                                    .filter(ScheduledStop.arrival_timestamp != None)
                                                    .filter(func.date(ScheduledStop.arrival_timestamp) == yesterday)
                                                    .statement
                                                    ,db.session.bind)

                elif period == "history":
                    arrivals_here = pd.read_sql(db.session.query(Trip.v, Trip.trip_id, Trip.pid, Trip.trip_id,
                                                                 ScheduledStop.trip_id, ScheduledStop.stop_id,
                                                                 ScheduledStop.stop_name, ScheduledStop.arrival_timestamp)
                                                    .join(ScheduledStop)
                                                    .filter(ScheduledStop.stop_id == stop)
                                                    .filter(ScheduledStop.arrival_timestamp != None)
                                                    .statement
                                                    ,db.session.bind)

                elif period is True:
                    try:
                        int(period)  # check if it digits (e.g. period=20180810)
                        request_date = datetime.datetime.strptime(args['period'], '%Y%m%d')  # make a datetime object
                        arrivals_here = pd.read_sql(db.session.query(Trip.v, Trip.trip_id, Trip.pid, Trip.trip_id,
                                                                     ScheduledStop.trip_id, ScheduledStop.stop_id,
                                                                     ScheduledStop.stop_name,
                                                                     ScheduledStop.arrival_timestamp)
                                                    .join(ScheduledStop)
                                                    .filter(ScheduledStop.stop_id == stop)
                                                    .filter(ScheduledStop.arrival_timestamp != None)
                                                    .filter(func.date(ScheduledStop.arrival_timestamp) == request_date)
                                                    .statement
                                                    , db.session.bind)

                    except ValueError:
                        pass
        except:

            # todo use this code to create an empty dummy dataframe?
            # arrivals_list_final_df = \
            #     pd.DataFrame(
            #         columns=['pkey', 'pt', 'rd', 'stop_id', 'stop_name', 'v', 'timestamp', 'delta'],
            #         data=[['0000000', '3', self.route, self.stop, 'N/A', 'N/A', datetime.time(0, 1),
            #                datetime.timedelta(seconds=0)]])

            pass


        # split final approach history (sorted by timestamp)
        # at each change in vehicle_id outputs a list of dfs
        # per https://stackoverflow.com/questions/41144231/python-how-to-split-pandas-dataframe-into-subsets-based-on-the-value-in-the-fir
        arrivals_here = timestamp_fix(arrivals_here,'arrival_timestamp')
        final_approach_dfs = [g for i, g in arrivals_here.groupby(arrivals_here['v'].ne(arrivals_here['v'].shift()).cumsum())]

        try:
            # take the last V(ehicle) approach in each df and add it to final list of arrivals
            arrivals_list_final_df = pd.DataFrame()
            for final_approach in final_approach_dfs:  # iterate over every final approach
                arrival_insert_df = final_approach.tail(1)  # take the last observation
                arrivals_list_final_df = arrivals_list_final_df.append(arrival_insert_df)  # insert into df

            # calc interval between last bus for each row, fill NaNs
            arrivals_list_final_df['delta']=(arrivals_list_final_df['timestamp'] - arrivals_list_final_df['timestamp'].shift(1)).fillna(0)

            # housekeeping ---------------------------------------------------

            # set stop_name
            stop_name = arrivals_list_final_df['stop_name'].iloc[0]

            # resort arrivals list
            # arrivals_list_final_df.sort_values("timestamp", inplace=True)

            return arrivals_list_final_df, stop_name

        except:
            arrivals_list_final_df=\
                pd.DataFrame(
                    columns=['pkey','pt','rd','stop_id','stop_name','v','timestamp','delta'],
                    data=[['0000000', '3', self.route, self.stop,'N/A', 'N/A', datetime.time(0,1), datetime.timedelta(seconds=0)]])
            stop_name = 'N/A'
            self.arrivals_table_time_created = datetime.datetime.now()
            return arrivals_list_final_df, stop_name

    #
    #
    # def get_hourly_frequency(self,route, stop, period):
    #     results = pd.DataFrame()
    #     self.arrivals_list_final_df['delta_int'] = self.arrivals_list_final_df['delta'].dt.seconds
    #
    #     try:
    #
    #         # results['frequency']= (self.arrivals_list_final_df.delta_int.resample('H').mean())//60
    #         results = (self.arrivals_list_final_df.groupby(self.arrivals_list_final_df.index.hour).mean())//60
    #         results = results.rename(columns={'delta_int': 'frequency'})
    #         results = results.drop(['pkey'], axis=1)
    #         results['hour'] = results.index
    #
    #     except TypeError:
    #         pass
    #
    #     except AttributeError:
    #         results = pd.DataFrame()
    #
    #     return results
    #
