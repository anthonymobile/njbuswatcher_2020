from datetime import datetime, time, timedelta
from dateutil import parser
from pathlib import Path
import json
import geojson
import pickle
import os, errno

from . import BusAPI, DataBases, Generators
from .wwwAPI import RouteReport

class TransitSystem:

    def __init__(self):

        # read the /config files -- grades, route metadata and overrides, collection metadata
        try:
            with open(self.get_abs_path()+ 'config/grade_descriptions.json') as f:
                self.grade_descriptions = json.load(f)
            with open(self.get_abs_path()+ 'config/route_descriptions.json') as f:
                self.route_descriptions = json.load(f)
            with open(self.get_abs_path()+ 'config/collection_descriptions.json') as f:
                self.collection_descriptions = json.load(f)
            with open(self.get_abs_path()+ 'config/period_descriptions.json') as f:
                self.period_descriptions = json.load(f)
            print ('<BUSWATCHER>All config files loaded')
        except:
            import sys
            sys.exit("<BUSWATCHER>One or more of the config files isn't loading properly")

        # load the route geometries
        self.route_geometries = self.get_route_geometries()
        self.routelist = self.get_routelist()
        self.grade_roster = self.get_grade_roster()

    def get_abs_path(self):
        if os.getcwd() == "/": # docker
            prefix = "buswatcher/buswatcher/"
        elif "Users" in os.getcwd():
            prefix = ""
        else:
            prefix=""
        return prefix

    def get_route_geometries(self):
        route_geometries={}
        for rd in self.route_descriptions['routedata']:
            # print('getting route geometry for '+rd['route'])
            route_geometries[rd['route']]={
                'route':rd['route'],
                'xml':self.get_single_route_xml(rd['route']),
                'paths': self.get_single_route_Paths(rd['route'])[0],
                'coordinate_bundle': self.get_single_route_Paths(rd['route'])[1]
            }
        return route_geometries

    def get_routelist(self):
        routelist = (list(set(r['route'] for r in self.route_descriptions['routedata'])))
        return routelist

    def get_single_route_xml(self,route):

        try:# load locally
            infile = (self.get_abs_path()+'config/route_geometry/' + route +'.xml')
            with open(infile,'rb') as f:
                data = f.read()
                return data

        except: #  if missing download and load
                # print ('fetching xmldata for '+route)
                route_xml = BusAPI.get_xml_data('nj', 'routes', route=route)
                outfile = (self.get_abs_path()+'config/route_geometry/' + route + '.xml')
                with open(outfile, 'wb') as f:  # overwrite existing file
                    f.write(route_xml)
                infile = (self.get_abs_path()+'config/route_geometry/' + route + '.xml')
                with open(infile, 'rb') as f:
                    return f.read()

    def get_single_route_Paths(self, route):
        while True:
            try:
                infile = (self.get_abs_path()+'config/route_geometry/' + route + '.xml')
                with open(infile, 'rb') as f:
                    return BusAPI.parse_xml_getRoutePoints(f.read())
            except:
                pass

    def get_single_route_paths_and_coordinatebundle(self, route):
        routes = self.route_geometries[route]['paths']
        coordinates_bundle = self.route_geometries[route]['coordinate_bundle']
        return routes, coordinates_bundle

    def get_single_route_stoplist_for_localizer(self, route):

        routedata, coordinate_bundle = self.get_single_route_paths_and_coordinatebundle(route)
        stoplist=[]
        for rt in routedata:
            for path in rt.paths:
                for p in path.points:
                    if p.__class__.__name__ == 'Stop':
                        stoplist.append(
                            {'stop_id': p.identity, 'st': p.st, 'd': p.d, 'lat': p.lat, 'lon': p.lon})
        return stoplist

    def get_single_route_stoplist_for_wwwAPI(self, route):
        route_stop_list = []

        for direction in self.get_single_route_Paths(route)[0]:
            path_list = []
            for path in direction.paths:
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

    def extract_geojson_features_from_system_map(self, route):
        waypoints_feature = geojson.Feature(geometry=json.loads(self.route_geometries[route]['coordinate_bundle']['waypoints_geojson']))
        stops_feature = geojson.Feature(geometry=json.loads(self.route_geometries[route]['coordinate_bundle']['stops_geojson']))
        # deleted line to BusAPI.parse_xml
        # stops_feature = json.loads(coordinate_bundle['waypoints_geojson'])
        # stops_feature = geojson.Feature(geometry=waypoints_feature)
        # stops_feature = json.loads(coordinate_bundle['stops_geojson'])
        # stops_feature = geojson.Feature(geometry=stops_feature)
        return waypoints_feature, stops_feature

    def render_geojson(self, args):

        try:
            # if we only want a single stop geojson
            if 'stop_id' in args.keys():
                # query the db and grab the lat lon for the first record that stop_id matches this one
                with DataBases.SQLAlchemyDBConnection() as db:
                    stop_query = db.session.query(
                        DataBases.ScheduledStop.stop_id,
                        DataBases.ScheduledStop.lat,
                        DataBases.ScheduledStop.lon) \
                        .filter(DataBases.ScheduledStop.stop_id == args['stop_id']) \
                        .first()
                    # format for geojson
                    stop_point = geojson.Point((float(stop_query[2]), float(stop_query[1])))
                    stop_feature = geojson.Feature(geometry=stop_point)
                    return stop_feature

            # otherwise continue to get waypoints/stops for all routes, one route
            elif 'rt' in args.keys():
                waypoints = []
                stops = []
                if args['rt'] == 'all':
                    for r in self.route_descriptions['routedata']:
                        waypoints_item, stops_item = self.extract_geojson_features_from_system_map(r['route'])
                        waypoints.append(waypoints_item)
                        stops.append(stops_item)
                else:
                    waypoints_item, stops_item = self.extract_geojson_features_from_system_map(args['rt'])
                    waypoints.append(waypoints_item)
                    stops.append(stops_item)

            # or a collection of routes
            elif 'collection' in args.keys():
                waypoints = []
                stops = []
                # pick the right collection

                for route in self.collection_descriptions[args['collection']]['routelist']:
                    waypoints_item, stops_item = self.extract_geojson_features_from_system_map(route)
                    waypoints.append(waypoints_item)
                    stops.append(stops_item)

            # now render the layers as geojson
            if args['layer'] == 'waypoints':
                waypoints_featurecollection = geojson.FeatureCollection(waypoints)
                return waypoints_featurecollection
            elif args['layer'] == 'stops':
                stops_featurecollection = geojson.FeatureCollection(stops)
                return stops_featurecollection

            return
        except:
            from flask import abort
            abort(404)
            pass

    def get_grade_roster(self):
        grade_roster=dict()
        for rt in self.routelist:
            report_fetcher = Generators.Generator()
            try:
                grade_report = report_fetcher.retrieve_json(rt, 'grade', 'year')
            except:
                pass
            grade_roster[rt]=grade_report['grade']
        return grade_roster


##################################################################
# Class TransitSystem bootstrappers
##################################################################

def flush_system_map():
    system_map_pickle_file = Path("config/system_map.pickle")

    try:
        os.remove(system_map_pickle_file)
    except OSError as e:
        if e.errno != errno.ENOENT:  # errno.ENOENT = no such file or directory
            raise  # re-raise exception if a different error occurred

    return

def load_system_map(**kwargs):

    pwd = os.getcwd()
    if os.getcwd() == "/":  # docker
        prefix = "buswatcher/buswatcher/"
    elif "Users" in os.getcwd(): # osx
        prefix = ""
    else: # linux
        prefix = ""

    # todo 0 add some kind of check to periodically reload the system map (or pass a kwarg
    # if kwargs['force_regenerate'] == True then TK

    system_map_pickle_file = Path(prefix+"config/system_map.pickle")
    try:
        my_abs_path = system_map_pickle_file.resolve(strict=True)
    except FileNotFoundError:
        system_map = TransitSystem()
        with open(system_map_pickle_file, "wb") as f:
            pickle.dump(system_map,f)
    else:
        with open(system_map_pickle_file, "rb") as f:
            system_map=pickle.load(f)

    return system_map

