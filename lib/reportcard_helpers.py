#
# database interactions
#

from lib import Buses, StopsDB
import sqlite3, datetime
import pandas as pd
import numpy as np

def db_setup(route):
    db = StopsDB.SQLite('data/%s.db' % route)
    conn = sqlite3.connect('data/%s.db' % route)
    return conn, db

def fetch_arrivals(source, route, flag):

    if flag is False:
        routedata = Buses.parse_route_xml(Buses.get_xml_data(source, 'routes', route=route))
        for i in routedata.paths:
            for p in i.points:
                if p.__class__.__name__ == 'Stop':
                    stoplist.append(p.identity)
        for s in stoplist:
            arrivals = Buses.parse_stopprediction_xml(Buses.get_xml_data('nj', 'stop_predictions', stop=s, route=route))
            # sys.stdout.write('.')
            now = datetime.datetime.now()
            db.insert_positions(arrivals, now)
        return

def get_stoplist(route):
    (conn, db) = db_setup(route)
    stoplist_query = (
            'SELECT stop_id FROM stop_predictions WHERE rd = %s GROUP BY stop_id;' % route)
    stoplist = pd.read_sql_query(stoplist_query, conn)
    return stoplist


#
# data transformations
#


def timestamp_fix(data):
    data['timestamp'] = data['timestamp'].str.split('.').str.get(0)
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    data = data.set_index('timestamp', drop=False)
    return data


#
# data views
#


def render_arrivals_history_full(source, route, stoplist):

    (conn, db) = db_setup(route)
    arrival_query = (
                'SELECT * FROM stop_predictions WHERE (rd = %s AND pt = "APPROACHING") ORDER BY stop_id,timestamp;' % route)
    df = pd.read_sql_query(arrival_query, conn)
    df = timestamp_fix(df)
    arrivals_history_full = []
    for s in stoplist:
        df_stop = df.loc[df.stop_id == s]
        df_stop['delta'] = df_stop['timestamp'] - df_stop['timestamp'].shift(1)
        for index, row in df_stop.iterrows():
            dict_ins = {}
            dict_ins['stop_id'] = row['stop_id']
            dict_ins['v'] = row['v']
            dict_ins['timestamp'] = row['timestamp']
            dict_ins['delta'] = row['delta']
            arrivals_history_full.append(dict_ins)
    return arrivals_history_full


def render_arrivals_hourly_mean(source, route, stoplist):

    (conn, db) = db_setup(route)
    arrival_query = (
            'SELECT * FROM stop_predictions WHERE (rd = %s AND pt = "APPROACHING") ORDER BY stop_id,timestamp;' % route)

    df = pd.read_sql_query(arrival_query, conn)

    df = timestamp_fix(df)

    arrivals_history_hourly = []

    for s in stoplist:

        df_stop = df.loc[df.stop_id == s]

        df_stop['delta'] = df_stop['timestamp'] - df_stop['timestamp'].shift(1)

        # resample hourly average
        # need to convert delta to numeric type first per...
        # https://stackoverflow.com/questions/44616546/finding-the-mean-and-standard-deviation-of-a-timedelta-object-in-pandas-df
        df_stop['delta_int'] = df_stop['delta'].values.astype(np.int64)
        for hour in df_stop.delta_int.resample('H').mean().iteritems():
            dict_ins = {}
            dict_ins['stop_id'] = s
            dict_ins['hour_top'] = hour[0]
            dict_ins['avg_interval'] = hour[1]
            arrivals_history_hourly.append(dict_ins)

    return arrivals_history_hourly
