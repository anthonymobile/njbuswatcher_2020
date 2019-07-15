# bug MDC fill in all short_descriptions in collection_definitions.json
# future graceful fall back to collections only if time to run main_loop is  > 1 min?
#
# usage:
# (statewide)                                           tripwatcher.py --statewide
# (only routes in defined collections)                  tripwatcher.py
#

import argparse
import time

from lib.RouteScan import RouteScan

from lib.TransitSystem import load_system_map, flush_system_map
from lib.CommonTools import timeit

@timeit
def main_loop(system_map):

    if args.collections_only is True:
        for collection,collection_description in system_map.collection_descriptions.items():
            for r in collection_description['routelist']:
                try:
                    RouteScan(system_map, r, args.statewide)
                except:
                    pass
    elif args.collections_only is False:
        RouteScan(system_map, 0, args.collections_only)
    return

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--collections', dest='collections_only', action='store_true', help='Watch only defined collections, not all NJ routes.')
    args = parser.parse_args()

    if args.collections_only is True:
        print('running in collections mode (watch all routes in all collections)')
    elif args.collections_only is False:
        print('running in statewide mode (watch all routes in NJ)')

    run_frequency = 60 # seconds
    time_start=time.monotonic()

    while True:
        system_map = load_system_map()
        scan = main_loop(system_map)
        # print('***sleeping***')
        time.sleep(run_frequency - ((time.monotonic() - time_start) % 60.0))  # sleep remainder of the 60 second loop




