# NJBuswatcher.com
# config

import json, sys
import buswatcher.lib.BusAPI as BusAPI


def load_config():
    with open('config/grade_descriptions.json') as f:
        grade_descriptions = json.load(f)['grade_descriptions']
    with open('config/route_definitions.json') as f:
        route_definitions = json.load(f)['route_definitions']
    with open('config/collection_descriptions.json') as f:
        collection_descriptions = json.load(f)['collection_descriptions']
    return route_definitions, grade_descriptions, collection_descriptions


def fetch_update_route_metadata():

    route_definitions, grade_descriptions, collection_descriptions = load_config()

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
        sys.stdout.write (r+'...')
        route_metadata = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data('nj', 'routes', route=r))
        route_entry = {'route': route_metadata[0][0].identity, 'nm': route_metadata[0][0].nm}
        api_response.append(route_entry)

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
            update = {"route": a['route'], "nm": a['nm'].split(' ', 1)[1], "ttl": "1d"}  # convert the tuple to a dict and
            print ("<<Added route record>>"+json.dumps(update))
            route_definitions.append(update) #add it to the route_definitions file so we dont scan it again until the TTL expires

    # delete existing route_definition.json and dump new complete as a json
    with open('config/route_definitions.json','w') as f:
        outdata = {'route_definitions':route_definitions}
        json.dump(outdata, f, indent=4)


    # with open('config/route_definitions.yml', 'w') as yaml_file:
    #     outdata = {'route_definitions':route_definitions}
    #     yaml.dump(outdata, yaml_file, default_flow_style=False)

    return


if __name__ == "__main__":

    route_definitions=load_config()[0]
    print ("loaded "+str(len(route_definitions))+" routes from route_definitions" )
    fetch_update_route_metadata()
    route_definition = load_config()[0]
    print ("loaded "+str(len(route_definitions))+" routes from route_definitions" )
