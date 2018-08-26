import pandas as pd
import StopsDB, BusAPI
import datetime
import requests
from geojson import Feature

class RouteReport:

    class Path():
        def __init__(self):
            self.name = 'Path'
            self.stops = []
            self.id = ''
            self.d = ''
            self.dd = ''

    def __init__(self, source, route, reportcard_routes,grade_descriptions,mapbox_access_key):

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
        self.get_routemap(mapbox_access_key)

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

        routedata = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data(self.source, 'routes', route=self.route))

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

    def get_routemap(self,mapbox_access_key):

        # 1 assemble the waypoint lat,long from self.route_stop_list into geoJSON format - just one direction for now
        geojson_route = []
        for stop in self.route_stop_list[0].stops:
            point = dict()
            point['lat'] = stop.lat
            point['long'] = stop.lon
            geojson_route.append(point)
        geojson_route = geojson_route[:25]

        # 2 create the route URL (point in ROUTE below = stop in route_stop_list above...- http://kazuar.github.io/visualize-trip-with-flask-and-mapbox/

        _route_url = "https://api.mapbox.com/directions/v5/mapbox/driving/{0}.json?access_token={1}&overview=full&geometries=geojson"


        # Create a string with all the geo coordinates
        lat_longs = ";".join(["{0},{1}".format(point["long"], point["lat"]) for point in geojson_route])
        # Create a url with the geo coordinates and access token
        routemap_url = _route_url.format(lat_longs, mapbox_access_key)

        result = requests.get(routemap_url)
        # Convert the return value to JSON
        data = result.json()

        # Create a geo json object from the routing data
        geometry = data["routes"][0]["geometry"]
        self.route_data = Feature(geometry=geometry, properties={})

        return

    # def get_buslocations_map_html(self):
    #
    #     # bus locations
    #     bus_position_reports = BusAPI.parse_xml_getBusesForRoute(BusAPI.get_xml_data('nj', 'buses_for_route', route=self.route))
    #     bus_current_latlons = []
    #
    #     for bus in bus_position_reports:
    #         if bus.rt == self.route:
    #             bus_current_latlons.append((float(bus.lat),float(bus.lon)))
    #     bus_current_lats, bus_current_lons = zip(*bus_current_latlons)
    #
    #     # Place map
    #     gmap = gmplot.GoogleMapPlotter(40.730026, -74.068776, 13, api_key)
    #     gmap.scatter(bus_current_lats, bus_current_lons, '#3B0B39', size=40, marker=True)
    #     hidden_gem_lat, hidden_gem_lon = 40.730026, -74.068776
    #     gmap.marker(hidden_gem_lat, hidden_gem_lon, 'cornflowerblue')
    #
    #     self.map_html = gmap.draw("raw.html")
    #
    #     return


class StopReport:

    def __init__(self,route,stop):

        # apply passed parameters to instance
        self.route=route
        self.stop=stop

        # database initialization
        self.db = StopsDB.MySQL('buses', 'buswatcher', 'njtransit', '127.0.0.1', self.route)
        self.conn = self.db.conn
        self.table_name = 'stop_approaches_log_' + self.route

        # populate stop report data
        self.get_arrivals(period='weekly') #todo DEPLOY change back to daily

    def get_arrivals(self, period): # should this move to a superclass since both RouteReport + StopReport will use it?
        # method 1: last approach in a contiguous sequence with 'approaching'

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
        df_temp = pd.read_sql_query(final_approach_query, self.conn) # todo arrivals table and deltas are all re-generated on the fly for every view now -- easier, but might lead to inconsistent/innaccurate results over time?
        df_temp = df_temp.drop(columns=['cars', 'consist', 'fd', 'm', 'name', 'rn', 'scheduled'])
        df_temp = timestamp_fix(df_temp)

        # split final approach history (sorted by timestamp) at each change in vehicle_id outputs a list of dfs -- per https://stackoverflow.com/questions/41144231/python-how-to-split-pandas-dataframe-into-subsets-based-on-the-value-in-the-fir
        final_approach_dfs = [g for i, g in df_temp.groupby(df_temp['v'].ne(df_temp['v'].shift()).cumsum())]

        # take the last V(ehicle) approach in each df and add it to final list of arrivals
        self.arrivals_list_final_df = pd.DataFrame()
        for final_approach in final_approach_dfs:  # iterate over every final approach
            arrival_insert_df = final_approach.tail(1)  # take the last observation
            self.arrivals_list_final_df = self.arrivals_list_final_df.append(arrival_insert_df)  # insert into df

        # log the time arrivals table was generated
        self.arrivals_table_time_created = datetime.datetime.now()

        # loop and calc delta for each row, fill NaNs
        self.arrivals_list_final_df['delta']=self.arrivals_list_final_df['timestamp']-self.arrivals_list_final_df['timestamp'].shift(1)
        self.arrivals_list_final_df['delta'].fillna(0) # todo NOW fill NaT with 0 <-- not workoing now

        return


def timestamp_fix(data): # trim the microseconds off the timestamp and convert it to datetime format

    data['timestamp'] = data['timestamp'].str.split('.').str.get(0)
    data['timestamp'] = pd.to_datetime(data['timestamp'],errors='coerce')
    data = data.set_index(pd.DatetimeIndex(data['timestamp']))

    # data = data.set_index(pd.DatetimeIndex(data['timestamp'], drop=False)

    return data

