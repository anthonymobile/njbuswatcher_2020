from datetime import datetime, time, timedelta
from dateutil import parser
from pathlib import Path
import json
import pickle
import sys

import buswatcher.lib.BusAPI as BusAPI
from buswatcher.lib.CommonTools import timeit


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
        except:
            print('cant find the files')

        # load the route geometries locally (to be deprecated)
        self.route_geometries = [({'route':r['route'], 'xml':get_route_geometry(r['route'])}) for r in self.route_descriptions['routedata']]

        # fetch the route geometries from NJT API
        print ('fetching route geometry XML from NJTransit')
        self.route_geometries_remote=dict()
        for r in self.route_descriptions['routedata']:
            try:
                self.route_geometries_remote[r['route']]=BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data('nj','routes',route=r['route']))
            except:
                pass

        # todo 0 compare self.route_geometries_local AND self.route_geometries_remote to make sure format is same

    def reset(self):
        # if its after 2am, before 4am, and reset hasn't been run, run it
        # n.b. this will only update if the trigger is fired (e.g. a page load)
        if ((self.reset_occurred == False) and ((is_time_between(time(2,00), time(4,00))==True))):
            # reset some values
            pass
        else:
            pass

    #method to return geojson -- stops, waypoints -- for a specific route
    def render_geojson(self,**kwargs):
        kwargs['rt']
        kwargs['layer']
        return

        # todo 0 FUNCTIONS TO MOVE INTO TransitSystem class as a Method, or replace
        # RouteReport.__get_stoplist(route)
        # API.__fetch_layers_json
        # API.get_map_layers
        # RouteConfig.maintenance_check
        # RouteConfig.load_config
        # RouteConfig.get_route_geometry
        # ? RouteConfig.fetch_update_route_metadata


# FUNCTIONS FOR THIS PROGRAM

def load_system_map():

    system_map_pickle_file = Path("config/system_map.pickle")

    try:
        my_abs_path = system_map_pickle_file.resolve(strict=True)
    except FileNotFoundError:
        new_map = TransitSystem()
        with open(system_map_pickle_file, "wb") as f:
            pickle.dump(new_map,f)
    else:
        with open(system_map_pickle_file, "rb") as f:
            new_map=pickle.load(f)

    return new_map

def maintenance_check(system_map):

    now=datetime.now()

    try:
        route_descriptions_last_updated = parser.parse(system_map.route_descriptions.last_updated)
    except:
        route_descriptions_last_updated = parser.parse('2000-01-01 01:01:01')
    route_descriptions_ttl = timedelta(seconds=int(system_map.route_descriptions['ttl']))

    # if TTL expired, update route geometry local XMLs
    if (now - route_descriptions_last_updated) > route_descriptions_ttl:
        update_route_descriptions_file(system_map)
        fetch_update_route_geometry(system_map)

    # generate bunching leaderboard
    # for r in route_definitions['route_definitons']:
    #     routereport.generate_bunching_leaderboard(route=rt_no['route'], period=period)

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
            route_metadata = BusAPI.parse_xml_getRoutePoints(get_route_geometry(r)) # this might not work if there isn't already a copy of the XML route data
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
            system_map.route_descriptions.append(update) #add it to the route_definitions file so we dont scan it again until the TTL expires

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

def fetch_update_route_geometry(system_map): # grabs a copy of the route XML to a file. this can probably be deprecated with TransitSystem now

    for r in system_map.route_descriptions['routedata']:
        try:
            route_xml =  BusAPI.get_xml_data('nj', 'routes', route=r['route'])
            sys.write.stdout('.')
        except:
            continue

        outfile = ('config/route_geometry/' + r['route'] +'.xml')
        with open(outfile,'wb') as f: # overwrite existing fille
            f.write(route_xml)
        # print ('dumped '+r['route'] +'.xml')
    return

def get_route_geometry(r):
    try:
        infile = ('config/route_geometry/' + r +'.xml')
        with open(infile,'rb') as f:
            return f.read()
    except: # if the xml for route r is missing, let's grab it (duplicated code here, but it works so...)

        route_xml = BusAPI.get_xml_data('nj', 'routes', route=r)

        outfile = ('config/route_geometry/' + r +'.xml')
        with open(outfile,'wb') as f: # overwrite existing fille
            f.write(route_xml)

        infile = ('config/route_geometry/' + r + '.xml')
        with open(infile, 'rb') as f:
            return f.read()

def is_time_between(begin_time, end_time, check_time=None):
    # If check time is not given, default to current UTC time
    check_time = check_time or datetime.utcnow().time()
    if begin_time < end_time:
        return check_time >= begin_time and check_time <= end_time
    else: # crosses midnight
        return check_time >= begin_time or check_time <= end_time



if __name__ == "__main__":

    system_map = load_system_map()


    # route_definitions=load_config()[0]
    # route_definitions = route_definitions['route_definitions'] # ignore the ttl, last_updated key:value pairs
    # print ("loaded "+str(len(route_definitions))+" routes from route_definitions" )
    #
    # route_definitions = load_config()[0]
    # route_definitions = route_definitions['route_definitions'] # ignore the ttl, last_updated key:value pairs
    # print ("loaded "+str(len(route_definitions))+" routes from route_definitions" )
