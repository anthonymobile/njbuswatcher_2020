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

import buswatcher.lib.Generators as Generators
from buswatcher.lib.DataBases import SQLAlchemyDBConnection, Trip, BusPosition, ScheduledStop
from buswatcher.lib.RouteConfig import load_system_map
from buswatcher.lib.CommonTools import timeit


@timeit # only need to isolate this in a function so we can timeit
def hourly_loop():

    if args.statewide is False:
        print ('run stuff from buswatcher.lib.Generators')
        # todo 1 delete and rebuild the system_map picklefile (build it first and swap, so it doesn't start looping.)

    elif args.statewide is True:
        print ('run stuff from buswatcher.lib.Generators')
    return

def hello(name):
    print
    "Hello %s!" % name


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

    # todo 1 come up a cron-like scheme
    #
    # 1 https://stackoverflow.com/questions/2398661/schedule-a-repeating-event-in-python-3#2399145
    # 2 https://apscheduler.readthedocs.io/en/3.0/


    # tasks that need to be run on a certain schedules
    # Generators.generate_headway_report(all) -- once per minute
    # Generators.generate_traveltime_report(all)  -- once every 15 minutes
    # Generators.generate_bunching_report(all) -- once per day


    run_frequency = 3600  # seconds, runs once per hour
    time_start = time.monotonic()

    while True:
        hourly_loop()
        print('***sleeping***')
        time.sleep(run_frequency - ((time.monotonic() - time_start) % run_frequency))  # sleep remainder of the 60 second loop



 # def is_time_between(begin_time, end_time, check_time=None):
#     # If check time is not given, default to current UTC time
#     check_time = check_time or datetime.utcnow().time()
#     if begin_time < end_time:
#         return check_time >= begin_time and check_time <= end_time
#     else: # crosses midnight
#         return check_time >= begin_time or check_time <= end_time
#

# def reset(self):
#     # if its after 2am, before 4am, and reset hasn't been run, run it
#     # n.b. this will only update if the trigger is fired (e.g. a page load)
#     if ((self.reset_occurred == False) and ((is_time_between(time(2,00), time(4,00))==True))):
#         # reset some values
#         pass
#     else:
#         pass

