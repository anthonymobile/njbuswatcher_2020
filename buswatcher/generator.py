# generator.py
#
# description:
# does hourly, daily RouteReport,StopReport generation to db or json so they don't run on page loads
#
# usage:
# (statewide)                                           generator.py --statewide
# (only routes in defined collections)                  generator.py
#
#
import argparse, time

from buswatcher.lib.Generators import *
from buswatcher.lib.DataBases import SQLAlchemyDBConnection, Trip, BusPosition, ScheduledStop
from buswatcher.lib.RouteConfig import load_system_map
from buswatcher.lib.CommonTools import timeit


@timeit # only need to isolate this in a function so we can timeit
def hourly_loop():

    if args.statewide is False:
        print ('do something')
    elif args.statewide is True:
        print ('do something')
    return

if __name__ == "__main__":

    system_map = load_system_map()

    # route_definitions = system_map.route_descriptions

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--statewide', dest='statewide', action='store_true', help='Watch all active routes in NJ. (requires lots of CPU).')
    args = parser.parse_args()

    if args.statewide is False:
        print('running in collections mode (watch all routes in all collections)')
    elif args.statewide is True:
        print('running in statewide mode (watch all routes in NJ)')

    # todo schedule this instead
    run_frequency = 3600 # seconds, runs once per hour
    time_start=time.monotonic()

    while True:
        hourly_loop()
        print('***sleeping***')
        time.sleep(run_frequency - ((time.monotonic() - time_start) % run_frequency))  # sleep remainder of the 60 second loop




