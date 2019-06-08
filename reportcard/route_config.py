# NJBuswatcher.com
# config

import json, sys
import lib.BusAPI as BusAPI


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
            rt = int(b)
            routes_active.append(b)
        except:
            continue
    routes_active.sort()

    # fetch route metadata
    rt_nm= list()
    for r in routes_active:
        sys.stdout.write (r+'...')
        route_metadata = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data('nj', 'routes', route=r))
        route_entry = {'rd': route_metadata[0][0].identity, 'nm': route_metadata[0][0].nm}
        rt_nm.append(route_entry)

    #todo 1 test new solution in this loop

    # merge API data into routes_definitions
    for updating in route_definitions: # iterate over existing route definitions
        for k,v in updating.items(): # iterate over keys in each route
            print ('k\t%a\tv\t%b\t').format(a=k, b=v)
            for i,j in rt_nm: # iterate over keys in data fetched from API
                print ('i\t%c\tj %d\t').format(c=i,d=j)
                if k == i: # if keys match
                    if v != j: # but values dont
                        print ('setting updating[%a] = %b').format(a=v,b=j)
                        updating[v] = j # update the updating value with the routes_active one

    # now go back and add any missing routes seen from API results to route_definitions
    for rt, nm in rt_nm:
        try:
            for r in route_definitions:
                if r['route'] == rt: # if so
                    r['nm'] = nm # update the name with API results (just in case)

        except: # if not
            update = {'route':rt_nm[0], "nm":rt_nm[0], "ttl":"1d"} # convert the tuple to a dict and
            route_definitions.append(update) #add it to the route_definitions file so we dont scan it again until the TTL expires

    # delete existing route_definition.json and dump new complete as a json
    with open('config/route_definitions.json','w') as f:
        outdata = {'route_definitions':route_definitions}
        json.dump(outdata, f)

    return


if __name__ == "__main__":

    route_definitions=load_config()[0]
    print ("loaded "+str(len(route_definitions))+" routes from route_definitions" )
    fetch_update_route_metadata()
    route_definition = load_config()[0]
    print ("loaded "+str(len(route_definitions))+" routes from route_definitions" )
