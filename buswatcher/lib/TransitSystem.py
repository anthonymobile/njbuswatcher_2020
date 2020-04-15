from pathlib import Path
import json
import datetime
import pickle
import os
import sys

from . import NJTransitAPI
from .CommonTools import get_config_path
from .DataBases import SQLAlchemyDBConnection

class SystemMap:
    def __init__(self):
        try:
            with open(get_config_path() + 'grade_descriptions.json') as f:
                self.grade_descriptions = json.load(f)
            with open(get_config_path() + 'route_descriptions.json') as f:
                self.route_descriptions = json.load(f)
            with open(get_config_path() + 'collection_descriptions.json') as f:
                self.collection_descriptions = json.load(f)
            with open(get_config_path() + 'period_descriptions.json') as f:
                self.period_descriptions = json.load(f)
        except:
            sys.exit("<BUSWATCHER>One or more of the config files isn't loading properly")
        self.route_geometries = self.get_route_geometries()
        self.routelist = self.get_routelist()
        self.db = SQLAlchemyDBConnection()

    def get_route_geometries(self):
        route_geometries={}
        for rd in self.route_descriptions['routedata']:
            xmldata = self.get_single_route_xml(rd['route'])
            if NJTransitAPI.validate_xmldata(xmldata) is True:
                route_geometries[rd['route']]={
                    'route':rd['route'],
                    'xml':xmldata,
                    'paths': NJTransitAPI.parse_xml_getRoutePoints(xmldata)[0],
                    'coordinate_bundle': NJTransitAPI.parse_xml_getRoutePoints(xmldata)[1]
                }
            else:
                print ('skipping route {} — bad XML'.format(rd['route']))
                continue
        return route_geometries

    def get_routelist(self):
        routelist = (list(set(r['route'] for r in self.route_descriptions['routedata'])))
        return routelist

    def get_single_route_xml(self,route):
        try:
            infile = (get_config_path() + 'route_geometry/' + route +'.xml')
            with open(infile,'rb') as f:
                data = f.read()
                return data
        except:
                route_xml = NJTransitAPI.get_xml_data('nj', 'routes', route=route)
                outfile = (get_config_path() + 'route_geometry/' + route + '.xml')
                with open(outfile, 'wb') as f:  # overwrite existing file
                    f.write(route_xml)
                infile = (get_config_path() + 'route_geometry/' + route + '.xml')
                with open(infile, 'rb') as f:
                    return f.read()

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

    def get_single_route_waypointlist_for_localizer(self, route):
        # this creates a waypoint list with a temporary sequence list for deciding bunching
        routedata, coordinate_bundle = self.get_single_route_paths_and_coordinatebundle(route)
        waypointlist=[]
        waypoint_id = 0
        for rt in routedata:
            for path in rt.paths:
                for p in path.points:
                    waypointlist.append(
                        {'waypoint_id': waypoint_id, 'd': p.d, 'lat': p.lat, 'lon': p.lon})
                    waypoint_id =+ 1
        return waypointlist


##################################################################
# Class TransitSystem bootstrappers
##################################################################

def flush_system_map():
    system_map_pickle_file = Path("config/system_map.pickle")
    try:
        os.remove(system_map_pickle_file)
        print ('deleted system_map.pickle file')
    except:
        print ('error. could NOT delete system_map.pickle file')
        pass
    load_system_map() # trigger a rebuild
    return

def find_pickle_file():
    # find the pickle file
    if os.getcwd() == "/":  # docker
        prefix = "/buswatcher/buswatcher/"
    elif "Users" in os.getcwd():  # osx
        prefix = ""
    else:  # linux & default
        prefix = ""
    pickle_filename = (prefix + "config/system_map.pickle")
    return {'prefix':prefix, 'pickle_filename':pickle_filename}

def load_system_map(**kwargs):
    pickle_filename = find_pickle_file()['pickle_filename']
    if 'force_regen' in kwargs.keys():
        if kwargs['force_regen'] == True:
            flush_system_map()
            system_map = SystemMap()
            with open(pickle_filename, "wb") as f:
                pickle.dump(system_map, f)
    try:
        with open(pickle_filename, "rb") as f:
            system_map = pickle.load(f)
            mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(pickle_filename)).strftime('%Y-%m-%d %H:%M:%S')
            print("Loading existing pickle file, last modified at " + mod_time)
    except FileNotFoundError:
        print(str(pickle_filename) + " pickle file not found. Rebuilding, may take a minute or so..")
        system_map = SystemMap()
        with open(pickle_filename, "wb") as f:
            pickle.dump(system_map, f)
    sys.stdout.write('watching routes ')
    for k,v in system_map.collection_descriptions.items():
        for r in v['routelist']:
            sys.stdout.write ('{} '.format(r))
    return system_map