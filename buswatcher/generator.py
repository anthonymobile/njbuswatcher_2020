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
from lib.RouteConfig import load_system_map
from lib.DBconfig import connection_string


####################################################################3
#   SCHEDULER SETUP
####################################################################3
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor,ProcessPoolExecutor

jobstores = {'default': SQLAlchemyJobStore(url=connection_string)}
executors = {'default': ThreadPoolExecutor(20)}
job_defaults = {'coalesce': True, 'max_instances': 5 }

def minute_tasks(system_map):
    # task_trigger_1 = HeadwayReport(system_map)
    print ('minute_tasks just ran')
    return

def quarter_hour_tasks(system_map):
    # task_trigger_1 = TravelTimeReport(system_map)
    print ('quarter_hour_tasks just ran')
    return

def hourly_tasks(system_map):
    task_trigger_1 = RouteUpdater(system_map) # refresh route descriptions
    task_trigger_2 = GradeReport().generate_reports() # refresh letter grades
    print ('hourly_tasks just ran')
    return

def daily_tasks(system_map):
    # Generators.generate_bunching_report(all) -- once per day at 2am
    task_trigger_1 = BunchingReport().generate_reports(system_map)
    print ('daily_tasks just ran')
    return


if __name__ == "__main__":

    system_map=load_system_map()
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--testmode', dest='test', action='store_true', help='Test mode, run the scheduled tasks in succession, bypassing apscheduler.')
    args = parser.parse_args()

    if args.test is True:
        minute_tasks(system_map)
        quarter_hour_tasks(system_map)
        hourly_tasks(system_map)
        daily_tasks(system_map)

    else:
        scheduler = BackgroundScheduler(jobstores=jobstores,executors=executors,job_defaults=job_defaults)
        system_map = load_system_map()

        scheduler.add_job(minute_tasks, 'interval', minutes=1, id='every minute', replace_existing=True)
        scheduler.add_job(quarter_hour_tasks, 'interval', minutes=15,id='every 15 minutes', replace_existing=True)
        scheduler.add_job(hourly_tasks, 'interval', minutes=60, id='every hour', replace_existing=True)
        scheduler.add_job(daily_tasks, trigger='cron', day='*', hour='2', id='every day at 2am', replace_existing=True)
        scheduler.start()
        scheduler.print_jobs()
        print ('generator will sleep now, while tasks run in the background')

        try:
            while True:
                time.sleep(2)
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()

