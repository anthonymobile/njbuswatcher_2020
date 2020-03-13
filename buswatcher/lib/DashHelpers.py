import pandas as pd
import pymysql as db
from sqlalchemy import create_engine


# todo many of these could use wwwAPI.RouteReport functions

def get_arrivals_hourly_histogram(route):

    # database variables
    user = 'buswatcher'
    password = 'njtransit'
    database = 'buses'

    db_connection_str = 'mysql+pymysql://{}:{}@localhost/{}'.format(user, password, database)
    engine = create_engine(db_connection_str)

    conn = connection = engine.connect()

    q = """
        SELECT scheduledstop_log.trip_id, trip_log.trip_id, scheduledstop_log.date, trip_log.rt, \
               scheduledstop_log.run, trip_log.pd, scheduledstop_log.v,  scheduledstop_log.stop_id, \
               scheduledstop_log.stop_name, scheduledstop_log.lat, scheduledstop_log.lon, \
               scheduledstop_log.arrival_timestamp
          FROM scheduledstop_log,trip_log
         WHERE scheduledstop_log.trip_id = trip_log.trip_id
           AND arrival_timestamp is not null 
           AND trip_log.rt = {};
    """.format(route)

    df = pd.read_sql_query(q, conn)
    df['hour_of_arrival_timestamp'] = df['arrival_timestamp'].dt.hour

    return df.groupby(['hour_of_arrival_timestamp']).size().to_frame(name = 'arrivals')



def get_arrivals_today_all(route, period):

    # database variables
    user = 'buswatcher'
    password = 'njtransit'
    database = 'buses'

    db_connection_str = 'mysql+pymysql://{}:{}@localhost/{}'.format(user, password, database)
    engine = create_engine(db_connection_str)

    conn = connection = engine.connect()

    period="""CURDATE() """

    q = """
    
        SELECT scheduledstop_log.trip_id, trip_log.trip_id, scheduledstop_log.date, trip_log.rt, \
           scheduledstop_log.run, trip_log.pd, scheduledstop_log.v,  scheduledstop_log.stop_id, \
           scheduledstop_log.stop_name, scheduledstop_log.lat, scheduledstop_log.lon, \
           scheduledstop_log.arrival_timestamp
      FROM scheduledstop_log,trip_log
     WHERE scheduledstop_log.trip_id = trip_log.trip_id
       AND arrival_timestamp is not null 
       AND DATE(arrival_timestamp) = {}
       AND trip_log.rt = {};

    """.format(period,route)

    df = pd.read_sql_query(q, conn)

    # todo add a column with headway from the previous arrival (use wwwAPI.RouteReport)

    return df
