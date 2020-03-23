# generator.py
#
# description:
# does hourly, daily RouteReport,StopReport generation to db or json so they don't run on page loads
#
# usage:
# bypasses apscheduler           generator.py --testmode
#                                generator.py
#
#
import argparse, time

from lib.Generators import RouteUpdater, GradeReport, BunchingReport, TraveltimeReport, HeadwayReport
from lib.TransitSystem import load_system_map, flush_system_map
from lib.DBconfig import connection_string
from lib.CommonTools import get_config_path

####################################################################3
#   SCHEDULER SETUP
####################################################################3
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor,ProcessPoolExecutor


# jobstore is in a sqlite file
# future move jobstore to mysql
db_url = (get_config_path()+'apscheduler.sqlite')
jobstores = {'default': SQLAlchemyJobStore(url='sqlite:///'+db_url)}

# settings
executors = {'default': ThreadPoolExecutor(20)}
job_defaults = {'coalesce': True, 'max_instances': 5 }

def minutely(system_map):
    # task_trigger_1 = HeadwayReport(system_map)
    print ('\nminute_tasks just ran')
    return

def quarter_hourly(system_map):
    # task_trigger_1 = TravelTimeReport(system_map)
    print ('\nquarter_hour_tasks just ran')
    return

def hourly(system_map):
    task_trigger_1 = RouteUpdater(system_map) # refresh route descriptions
    task_trigger_2 = flush_system_map() # delete and rebuild the system map
    print ('\nhourly_tasks just ran')

    return

def daily(system_map):
    # runs at 2am
    task_trigger_1 = BunchingReport().generate_reports(system_map) # rebuild bunching reports
    task_trigger_2 = GradeReport().generate_reports(system_map) # rebuild grade report
    task_trigger_3 = flush_system_map() # delete and rebuild the system map
    task_trigger_4 = load_system_map(force_regen=True) # regenerate the new system map pickle (re-downloads XML route points and fetches new grades)

    print ('\ndaily_tasks just ran')
    return

def initialize_scheduler(system_map):

    scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults)
    scheduler.add_job(minutely, 'interval', minutes=1, id='every minute', replace_existing=True, args=[system_map])
    scheduler.add_job(quarter_hourly, 'interval', minutes=15, id='every 15 minutes', replace_existing=True,
                      args=[system_map])
    scheduler.add_job(hourly, 'interval', minutes=60, id='every hour', replace_existing=True, args=[system_map])
    scheduler.add_job(daily, 'cron', day='*', hour='2', id='every day at 2am', replace_existing=True, args=[system_map])
    scheduler.start()
    scheduler.print_jobs()
    print('generator will sleep now, while tasks run in the background')
    return scheduler


if __name__ == "__main__":

    system_map = load_system_map()

    parser = argparse.ArgumentParser()
    parser.add_argument('--production', dest='production', action='store_true',help='Production mode, run all tasks, reverse chrono order, then start schedule.')
    parser.add_argument('--test', dest='test', action='store_true', help='Test mode, run the scheduled tasks in succession, bypassing schedule.')
    parser.add_argument("--tasks", nargs='*', help="List of tasks you want to run")
    args = parser.parse_args()

    # check if we are in production mode
    if args.production is True:
        # if true,
        tasks=['daily','hourly','quarter_hourly','minutely']
        for task in tasks:
            func = locals()[task](system_map)
            func
        scheduler = initialize_scheduler(system_map)

        # then hold
        try:
            while True:
                time.sleep(2)
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()

    # or if we are testing
    elif args.test is True:
        for arg in args.tasks:
            func = locals()[arg](system_map)
            func

