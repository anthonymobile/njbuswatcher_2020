#
# usage:
# (statewide)                                           tripwatcher.py --statewide
# (only routes in defined collections)                  tripwatcher.py
#

import argparse
import time

import RouteScan

from RouteConfig import load_system_map, flush_system_map,maintenance_check
from CommonTools import timeit

@timeit
def main_loop(system_map):

    if args.statewide is False:
        for collection,collection_description in system_map.collection_descriptions.items():
            for r in collection_description['routelist']:
                try:
                    RouteScan(system_map, r, args.statewide)
                except:
                    pass
    elif args.statewide is True:
        RouteScan(system_map, 0, args.statewide)
    return

if __name__ == "__main__":


    flush_system_map()
    system_map=load_system_map()
    # route_definitions, grade_descriptions, collection_descriptions = load_config()
    # route_definitions = route_definitions['route_definitions'] # ignore the ttl, last_updated key:value pairs

    # maintenance check
    maintenance_check(system_map)

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--statewide', dest='statewide', action='store_true', help='Watch all active routes in NJ. (requires lots of CPU).')
    args = parser.parse_args()

    if args.statewide is False:
        print('running in collections mode (watch all routes in all collections)')
    elif args.statewide is True:
        print('running in statewide mode (watch all routes in NJ)')

    run_frequency = 60 # seconds
    time_start=time.monotonic()

    while True:
        scan = main_loop(system_map)
        # print('***sleeping***')
        time.sleep(run_frequency - ((time.monotonic() - time_start) % 60.0))  # sleep remainder of the 60 second loop




