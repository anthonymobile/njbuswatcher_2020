# NJBuswatcher.com
# config

import json, sys
import buswatcher.lib.BusAPI as BusAPI
from dateutil import parser
from datetime import datetime, timedelta

from buswatcher.lib.CommonTools import timeit

def load_config():

    with open('config/grade_descriptions.json') as f: #todo 0 this should load the grade_descriptions as a dict, not a list (restructure grade_description.json) and rewrite everything that references it
        grade_descriptions = json.load(f)['grade_descriptions']

    with open('config/route_definitions.json') as f:
        route_definitions = json.load(f)

    with open('config/collection_descriptions.json') as f: #todo 0 this should load the collections as a dict, not a list (restructure collection_description.json) and rewrite everything that references it
        collection_descriptions = json.load(f)['collection_descriptions']

    return route_definitions, grade_descriptions, collection_descriptions

def maintenance_check():

    now=datetime.now()

    # update route definitions
    route_definitions, a, b = load_config()
    try:
        route_definitions_last_updated = parser.parse(route_definitions['last_updated'])
    except:
        route_definitions_last_updated = parser.parse('2000-01-01 01:01:01')
    route_definitions_ttl = timedelta(seconds=int(route_definitions['ttl']))
    if (now - route_definitions_last_updated) > route_definitions_ttl:
        fetch_update_route_metadata()

        # update route geometry local XMLs
        fetch_update_route_geometry()


    # additional maintenance task
    # for r in route_definitions['route_definitons']:
    #     # create base RouteReport instance
    #     routereport = wwwAPI.RouteReport(source, rt_no['route'])

    # additional maintenance task
    # for r in route_definitions['route_definitons']:
    #     # generate bunching leaderboard
    #     routereport.generate_bunching_leaderboard(route=rt_no['route'], period=period)
    #     # generate other reports
    #     # e.g. routereport.get_bunching_leaderboard()
    return

def fetch_update_route_metadata():

    # add a try-except to catch JSON file errors here
    route_definitions, grade_descriptions, collection_descriptions = load_config()
    route_definitions = route_definitions['route_definitions'] # ignore the ttl, last_updated key:value pairs

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
        for r in route_definitions:  # iterate over defined routes
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
        for r in route_definitions:
            if r['route'] == a['route']:
                matched = True
        if matched == False:
            print ("no match for route "+a['route']+" in route_definitions")
            update = {"route": a['route'], "nm": a['nm'].split(' ', 1)[1], "ttl": "1d","description_long": "", "description_short": "", "frequency": "low", "prettyname": "",
                      "schedule_url": "https://www.njtransit.com/sf/sf_servlet.srv?hdnPageAction=BusTo"}
            print ("<<Added route record>>"+json.dumps(update))
            route_definitions.append(update) #add it to the route_definitions file so we dont scan it again until the TTL expires

    # make one last scan of file --  if prettyname in file is blank, should copy nm from file to prettyname
    for route in route_definitions:
        if route['prettyname'] == "":
            route['prettyname'] = route['nm']

    # create data to dump with last_updated and ttl
    outdata = dict()
    now = datetime.now()
    outdata['last_updated'] = now.strftime("%Y-%m-%d %H:%M:%S")
    outdata['ttl'] = '86400'
    outdata['route_definitions'] = route_definitions

    # delete existing route_definition.json and dump new complete as a json
    with open('config/route_definitions.json','w') as f:
        json.dump(outdata, f, indent=4)


    return

def fetch_update_route_geometry(): # grabs a copy of the route XML for all defined routes # rewrite this to store in database table as XML or JSON objects... or after it is parsed as a picklefile?

    route_definitions, a, b = load_config()

    for r in route_definitions['route_definitions']:
        try:
            route_xml =  BusAPI.get_xml_data('nj', 'routes', route=r['route'])
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

if __name__ == "__main__":

    route_definitions=load_config()[0]
    route_definitions = route_definitions['route_definitions'] # ignore the ttl, last_updated key:value pairs
    print ("loaded "+str(len(route_definitions))+" routes from route_definitions" )
    fetch_update_route_metadata()

    route_definitions = load_config()[0]
    route_definitions = route_definitions['route_definitions'] # ignore the ttl, last_updated key:value pairs
    print ("loaded "+str(len(route_definitions))+" routes from route_definitions" )
