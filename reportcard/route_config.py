# NJBuswatcher.com
# config

# todo finish testing the route_config.py loader

import json, sys
import lib.BusAPI as BusAPI


def load_route_grade_metadata():
    # todo figure out which JSON format is better (grades, or routes)

    with open('config/grade_descriptions.json') as f:
        grade_descriptions = json.load(f)

    with open('config/route_definitions.json') as f:
        route_definitions = json.load(f)

    return route_definitions, grade_descriptions


def fetch_update_route_metadata():

    route_definitions, grade_definitions = load_route_grade_metadata()

    # todo 1 add any routes in retrieved list from API not in OVERRIDES

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
            rt = int(b)
            routes_active.append(b)
        except:
            continue
    routes_active.sort()

    # fetch route metadata
    rt_nm= list()
    for r in routes_active:
        # todo can i get this data with a less data-intensive API call?
        sys.stdout.write (r+'...')
        route_metadata = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data('nj', 'routes', route=r))
        route_entry = {'rd': route_metadata[0][0].identity, 'uglyname': route_metadata[0][0].nm}
        rt_nm.append(route_entry)

    # merge API data into routes_definitions
    for updating in route_definitions['routes'].iteritems(): # iterate over existing route defintions
        for k,v in updating.iteritems(): # iterate over keys in each route
            for i,j in routes_active.iteritems(): # iterate over keys in data fetched from API
                if k == i: # if keys match
                    if v != j: # but values dont
                        v = j # update the updating value with the routes_active one

    # now go back and add any missing routes seen from API to route_definitions
    for route in routes_active.iteritems():
        if route['route'] not in route_definitions['routes'].values():
            route_definitions[route['route']] = route # add that one to the route defitionsl
    # dump routes_definitions.json, overwriting
    with open('config/route_definitions.json') as f:
        json.dump(route_definitions, f)

    return


if __name__ == "__main__":

    route_definitions, grade_descriptions=load_route_grade_metadata()
    print (len(route_definitions['routes']))
    fetch_update_route_metadata()
    route_definitions, grade_descriptions = load_route_grade_metadata()
    print (len(route_definitions['routes']))

