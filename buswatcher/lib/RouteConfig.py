from datetime import datetime, time, timedelta
from dateutil import parser
from pathlib import Path
import json
import geojson
import pickle
import os, errno

import buswatcher.lib.BusAPI as BusAPI
# from buswatcher.lib.DataBases import SQLAlchemyDBConnection
import buswatcher.lib.DataBases as DataBases
from buswatcher.lib.wwwAPI import RouteReport

class TransitSystem:

    def __init__(self):

        # read the /config files -- grades, route metadata and overrides, collection metadata
        try:
            with open('config/grade_descriptions.json') as f:
                self.grade_descriptions = json.load(f)
            with open('config/route_descriptions.json') as f:
                self.route_descriptions = json.load(f)
            with open('config/collection_descriptions.json') as f:
                self.collection_descriptions = json.load(f)
            with open('config/period_descriptions.json') as f:
                self.period_descriptions = json.load(f)
        except:
            print("One or more of the config files isn't loading properly")

        # load the route geometries
        self.route_geometries = self.get_route_geometries()
        self.routelist = self.get_routelist()

    def get_route_geometries(self):
        route_geometries={}
        for routedata in self.route_descriptions['routedata']:
            route_geometries[routedata['route']]={
                'route':routedata['route'],
                'xml':self.get_single_route_xml(routedata['route']),
                'paths': self.get_single_route_Paths(routedata['route'])[0],
                'coordinate_bundle': self.get_single_route_Paths(routedata['route'])[1]
            }
        return route_geometries


    def get_routelist(self):
        routelist = (list(set(r['route'] for r in self.route_descriptions['routedata'])))
        return routelist

    def get_single_route_xml(self,route):

        try:# load locally
            infile = ('config/route_geometry/' + route +'.xml')
            with open(infile,'rb') as f:
                return f.read()
        except: #  if missing download and load
            route_xml = BusAPI.get_xml_data('nj', 'routes', route=route)
            outfile = ('config/route_geometry/' + route + '.xml')
            with open(outfile, 'wb') as f:  # overwrite existing file
                f.write(route_xml)
            infile = ('config/route_geometry/' + route + '.xml')
            with open(infile, 'rb') as f:
                return f.read()

    def get_single_route_Paths(self, route):
        try:
            infile = ('config/route_geometry/' + route + '.xml')
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
                stop_coordinates = [float(stop_query[2]), float(stop_query[1])]
                stop_geojson = geojson.Point(stop_coordinates)
                # stop_featurecollection = geojson.FeatureCollection(stop_geojson)
                stop_featurecollection = geojson.Feature(stop_geojson)

                return stop_featurecollection

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
            # for c in self.collection_descriptions:
            #     if c['collection_url'] == args['collection']:
            #         for r in c['routelist']:
            #             waypoints_item, stops_item = self.extract_geojson_features_from_system_map(r)
            #             waypoints.append(waypoints_item)
            #             stops.append(stops_item)


        # now render the layers as geojson
        if args['layer'] == 'waypoints':
            waypoints_featurecollection = geojson.FeatureCollection(waypoints)
            return waypoints_featurecollection
        elif args['layer'] == 'stops':
            stops_featurecollection = geojson.FeatureCollection(stops)
            return stops_featurecollection

        return


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

def load_system_map():

    system_map_pickle_file = Path("config/system_map.pickle")
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



# def get_route_xml(r): # create a system_map and then pulls a single route from it
#     try:
#         # load the system_map
#         system_map = load_system_map()
#         # fetch the right system_map['route_geomtries']['xml']
#         return [x['xml'] for x in system_map.route_geometries if x['route'] == r]
#
#         # infile = ('config/route_geometry/' + r +'.xml')
#         # with open(infile,'rb') as f:
#         #     return f.read()
#
#     except: # if its not in the system_map, fetch the XML and return that instead
#
#         route_xml = BusAPI.get_xml_data('nj', 'routes', route=r)
#
#         outfile = ('config/route_geometry/' + r +'.xml')
#         with open(outfile,'wb') as f: # overwrite existing fille
#             f.write(route_xml)
#
#         infile = ('config/route_geometry/' + r + '.xml')
#         with open(infile, 'rb') as f:
#             return f.read()

##################################################################
# MISC FUNCTIONS
##################################################################


def maintenance_check(system_map): #todo 4 move to Generators / generator.py

    now=datetime.now()

    try:
        route_descriptions_last_updated = parser.parse(system_map.route_descriptions['last_updated'])
    except:
        route_descriptions_last_updated = parser.parse('2000-01-01 01:01:01')
    route_descriptions_ttl = timedelta(seconds=int(system_map.route_descriptions['ttl']))

    # if TTL expired, update route geometry local XMLs
    if (now - route_descriptions_last_updated) > route_descriptions_ttl:
        update_route_descriptions_file(system_map)
        # fetch_update_route_geometry(system_map)



    return

def update_route_descriptions_file(system_map):

    # add a try-except to catch JSON file errors here
    # route_definitions, grade_descriptions, collection_descriptions = load_config()
    # route_definitions = route_definitions['route_definitions'] # ignore the ttl, last_updated key:value pairs

    print ('Updating route_descriptions.json')
    # UPDATE ROUTES FROM API

    # get list of active routes
    buses = BusAPI.parse_xml_getBusesForRouteAll(BusAPI.get_xml_data('nj', 'all_buses'))
    routes_active_tmp = [b.rt for b in buses]

    # sort by freq (not needed, but useful) and remove dupes
    routes_active_tmp_sorted_unique = sorted(set(routes_active_tmp), key=lambda ele: routes_active_tmp.count(ele))

    # remove any bus not on a numeric route
    routes_active = list()
    for b in routes_active_tmp_sorted_unique:
        try:
            dummy = int(b)
            routes_active.append(b)
        except:
            continue
    routes_active.sort()

    # fetch route metadata
    api_response= list()
    for r in routes_active:

        try:
            route_metadata = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data('nj','routes',route=r))
            route_entry = {'route': route_metadata[0][0].identity,'nm': route_metadata[0][0].nm}
            api_response.append(route_entry)
        except:
            pass

    # merge API data into routes_definitions
    for a in api_response: # iterate over routes fetched from API
        for r in system_map.route_descriptions['routedata']:  # iterate over defined routes
            if a['route'] == r['route']:  # match on route number
                for k,v in a.items():  # then iterate over API response keys
                    try:
                        if r[k] != v:  # if the value from the API response is different
                            r[k] = v.split(' ', 1)[1]  # update the defined routes value with the API response one, splitting the route number off the front
                    except: # if the r[k] key is missing
                        r[k] = v.split(' ', 1)[1]

    # now go back and add any missing routes seen from API results to route_definitions
    for a in api_response:
        matched = False
        for r in system_map.route_descriptions['routedata']:
            if r['route'] == a['route']:
                matched = True
        if matched == False:
            print ("no match for route "+a['route']+" in route_definitions")
            update = {"route": a['route'], "nm": a['nm'].split(' ', 1)[1], "ttl": "1d","description_long": "", "description_short": "", "frequency": "low", "prettyname": "",
                      "schedule_url": "https://www.njtransit.com/sf/sf_servlet.srv?hdnPageAction=BusTo"}
            print ("<<Added route record>>"+json.dumps(update))
            system_map.route_descriptions['routedata'].append(update) #add it to the route_definitions file so we dont scan it again until the TTL expires

    # make one last scan of file --  if prettyname in file is blank, should copy nm from file to prettyname
    for route in system_map.route_descriptions['routedata']:
        if route['prettyname'] == "":
            route['prettyname'] = route['nm']

    # create data to dump with last_updated and ttl
    outdata = dict()
    now = datetime.now()
    outdata['last_updated'] = now.strftime("%Y-%m-%d %H:%M:%S")
    outdata['ttl'] = '86400'
    outdata['routedata'] = system_map.route_descriptions['routedata']

    # delete existing route_definition.json and dump new complete as a json
    with open('config/route_descriptions.json','w') as f:
        json.dump(outdata, f, indent=4)

    return







