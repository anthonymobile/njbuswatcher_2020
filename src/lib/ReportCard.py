import pandas as pd
import StopsDB, BusAPI
import datetime
from mapbox import Directions
from geojson import Point
import config
import sys

class RouteReport:

    class Path():
        def __init__(self):
            self.name = 'Path'
            self.stops = []
            self.id = ''
            self.d = ''
            self.dd = ''

    def __init__(self, source, route, reportcard_routes,grade_descriptions):

        # apply passed parameters to instance
        self.source = source
        self.route = route
        self.reportcard_routes = reportcard_routes
        self.grade_descriptions = grade_descriptions

        # database initialization
        self.db = StopsDB.MySQL('buses', 'buswatcher', 'njtransit', '127.0.0.1', self.route)
        self.conn = self.db.conn
        self.table_name = 'stop_approaches_log_' + self.route

        # populate report card data
        self.get_routename()
        self.compute_grade()
        self.get_stoplist()
        self.get_bunching_badboys()

        # map stuff TODOMAP activate map __init__
        # self.get_route_waypoints()
        # self.get_current_buslocations_geojson()

    def get_routename(self):
        routedata = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data(self.source, 'routes', route=self.route))
        self.routename=routedata[0].nm
        return


    def compute_grade(self):
        # for now, grade is coded manually in route_config.py
        # FUTURE fancier grade calculation based on historical data
        for route in self.reportcard_routes:
            if route['route'] == self.route:
                self.grade = route['grade']
                self.description_long = route['description_long']
                for entry in self.grade_descriptions:
                    if self.grade == entry['grade']:
                        self.grade_description = entry['description']
                    else:
                        pass
                if not self.grade_description:
                    grade_description = 'Cannot find a description for that grade.'
                else:
                    pass
            else:
                pass
        return


    def get_stoplist(self):
        routedata = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data(self.source, 'routes', route=self.route)) # todo BUG why getting inconsistent service lists back from this? hardcode them instead?
        route_stop_list_temp = []
        for r in routedata:
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
            route_stop_list_temp.append(path_list)
        self.route_stop_list = route_stop_list_temp[0] # transpose a single copy since the others are all repeats (can be verified by path ids)
        return

    def get_bunching_badboys(self): #todo NOW1 bunching analysis WTD?
        # generates top 10 list of stops on the route by # of bunching incidents in last week

        self.bunching_badboys = []

        # loop over each service and stop
        bunch_total=0
        print 'starting daily bunching analysis...'
        for service in self.route_stop_list:
            for stop in service.stops:
                print stop.identity,
                try:
                    report=StopReport(self.route,stop.identity,'daily')
                except:
                    pass

                # calculate number of bunches
                for (index, row) in report.arrivals_list_final_df.iterrows(): # TODOD DEBUGGING HERE
                    if (row.delta > report.bigbang) and (row.delta <= report.bunching_interval):
                        bunch_total += 1
                        sys.stdout.write('.'),
                print
            # append tuple to the list
            self.bunching_badboys.append((stop.st, bunch_total))

        # sort stops by number of bunchings, grad first 10
        self.bunching_badboys.sort(key=bunch_total, reverse=True)
        self.bunching_badboys=self.bunching_badboys[:10]

        return

    def get_route_waypoints(self):

        # TODOMAP check to see if the geojson file exists and is less than 24 hours old

        # 1 create list of waypoints in geoJSON
        # from self.route_stop_list
        # just 1 direction for now (will need to pass service if i want something more accurate)

        route_latlons=[]
        for stop in self.route_stop_list[0].stops:
            route_latlons.append((stop.lat,stop.lon))


        # sample 20 waypoints evenly spaced, plus the last one
        n = len(route_latlons) / 20 # could be 24 if mapbox allows
        chunks = [route_latlons[i:i + n] for i in xrange(0, len(route_latlons), n)]
        route_latlons_sample=[]
        for chunk in chunks:
            route_latlons_sample.append(chunk[0]) # first item of each chunk
            route_latlons_sample.append(route_latlons[-1]) #last item for total of 21 waypoints

        # format as geoJson
        route_latlons_sample_lats, route_latlons_sample_lons = zip(*route_latlons_sample)
        route_waypoints_geojson=dict()
        for x in range(0,len(route_latlons_sample_lats)):
            insertion = Point((route_latlons_sample_lats[x],route_latlons_sample_lons[x])) # TODOMAP DEBUGGING HERE "not a JSON compliant number"
            route_waypoints_geojson.update(insertion)

        # get the route features from MapBox API
        service = Directions(access_token=config.mapbox_access_key)
        mapbox_response = service.directions([route_waypoints_geojson],'mapbox.driving')
        self.route_geojson = mapbox_response.geojson()

        # TODOMAP dump it to a file. then the javascript loads the file and draws the points

        return


    def get_current_buslocations_geojson(self):

        # get raw bus locations
        bus_position_reports = BusAPI.parse_xml_getBusesForRoute(BusAPI.get_xml_data('nj', 'buses_for_route', route=self.route))

        self.current_buslocations_geojson = []

        # populate
        for bus in bus_position_reports:
            if bus.rt == self.route:
                point = dict()
                point['lat'] = float(bus.lat)
                point['long'] = float(bus.lon)
                self.current_buslocations_geojson.append(point)
        self.current_buslocations_geojson_timestamp=datetime.datetime.now()

        return


class StopReport:

    def __init__(self,route,stop,period):
        # apply passed parameters to instance
        self.route=route
        self.stop=stop
        self.period=period
        # database initialization
        self.db = StopsDB.MySQL('buses', 'buswatcher', 'njtransit', '127.0.0.1', self.route)
        self.conn = self.db.conn
        self.table_name = 'stop_approaches_log_' + self.route
        # populate stop report data
        self.get_arrivals(self.period)


    def get_arrivals(self, period):
        self.arrivals_table_time_created = None
        self.period = period
        if period == "daily":
            final_approach_query = ('SELECT * FROM %s WHERE (stop_id= %s AND pt = "APPROACHING" AND DATE(`timestamp`)=CURDATE() ) ORDER BY timestamp DESC;' % (self.table_name, self.stop))
        elif period=="weekly":
            final_approach_query = ('SELECT * FROM %s WHERE (stop_id= %s AND pt = "APPROACHING" AND (YEARWEEK(`timestamp`, 1) = YEARWEEK(CURDATE(), 1))) ORDER BY timestamp DESC;' % (self.table_name,self.stop))
        elif period=="history":
            final_approach_query = ('SELECT * FROM %s WHERE (stop_id= %s AND pt = "APPROACHING") ORDER BY timestamp DESC;' % (self.table_name,self.stop))
        else:
            raise RuntimeError('Bad request sucker!')

        # get data and basic cleanup
        df_temp = pd.read_sql_query(final_approach_query, self.conn) # arrivals table and deltas are all re-generated on the fly for every view now -- easier, but might lead to inconsistent/innaccurate results over time?
        df_temp = df_temp.drop(columns=['cars', 'consist', 'fd', 'm', 'name', 'rn', 'scheduled'])
        df_temp = timestamp_fix(df_temp)

        # split final approach history (sorted by timestamp) at each change in vehicle_id outputs a list of dfs -- per https://stackoverflow.com/questions/41144231/python-how-to-split-pandas-dataframe-into-subsets-based-on-the-value-in-the-fir
        final_approach_dfs = [g for i, g in df_temp.groupby(df_temp['v'].ne(df_temp['v'].shift()).cumsum())]

        # take the last V(ehicle) approach in each df and add it to final list of arrivals
        self.arrivals_list_final_df = pd.DataFrame()
        for final_approach in final_approach_dfs:  # iterate over every final approach
            arrival_insert_df = final_approach.tail(1)  # take the last observation
            self.arrivals_list_final_df = self.arrivals_list_final_df.append(arrival_insert_df)  # insert into df

        # calc interval between last bus for each row, fill NaNs
        self.arrivals_list_final_df['delta']=(self.arrivals_list_final_df['timestamp'] - self.arrivals_list_final_df['timestamp'].shift(-1)).fillna(0)

        # housekeeping ---------------------------------------------------
        # log the time arrivals table was generated
        self.arrivals_table_time_created = datetime.datetime.now()
        # set stop_name
        self.stop_name = self.arrivals_list_final_df['stop_name'].iloc[0]
        # set timedelta constant for later use in bunching analysis
        self.bunching_interval = datetime.timedelta(minutes=3)
        # set a timedelta for zero
        self.bigbang = datetime.timedelta(seconds=0)

        return

# common functions
def timestamp_fix(data): # trim the microseconds off the timestamp and convert it to datetime format
    data['timestamp'] = data['timestamp'].str.split('.').str.get(0)
    data['timestamp'] = pd.to_datetime(data['timestamp'],errors='coerce')
    data = data.set_index(pd.DatetimeIndex(data['timestamp']))
    # data = data.set_index(pd.DatetimeIndex(data['timestamp'], drop=False)
    return data

