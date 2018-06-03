#
# database interactions
#


import sqlite3, datetime, sys

import numpy as np
import pandas as pd
pd.set_option('display.width', 1000)

from lib import Buses, StopsDB

def db_setup(route):
    db = StopsDB.SQLite('data/%s.db' % route)
    conn = sqlite3.connect('data/%s.db' % route)
    return conn, db

def fetch_arrivals(source, route):

    (conn, db) = db_setup(route)

    routedata = Buses.parse_route_xml(Buses.get_xml_data(source, 'routes', route=route))

    stoplist = []

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

    return stoplist['stop_id']


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
            try:
                dict_ins['delta'] = row['delta'].seconds
            except:
                dict_ins['delta'] = row['delta']
            arrivals_history_full.append(dict_ins)

    return arrivals_history_full

def render_arrivals_history_1stop(source, route, stop):

    (conn, db) = db_setup(route)

    arrival_query = (
                'SELECT * FROM stop_predictions WHERE (rd = %s AND pt = "APPROACHING" AND stop_id= %s ) ORDER BY stop_id,timestamp;' % (route, stop))

    df = pd.read_sql_query(arrival_query, conn)

    df = timestamp_fix(df)

    #
    # drop all but the last row from each cluster of buses
    # slicing by vehicle number wont work because same vehicle may have stopped at that stop many times in history... and there is no run number... so need to look for time gaps?

    # 2018-05-30 18:30:42  OBSERVER HWY + WASHINGTON ST  5708 2018-05-30 18:30:42
    # 2018-05-30 18:31:09  OBSERVER HWY + WASHINGTON ST  5708 2018-05-30 18:31:09
    # 2018-05-30 18:33:52  OBSERVER HWY + WASHINGTON ST  5708 2018-05-30 18:33:52 <--- keep this one



    #
    # debugging loop----------------------------------------------------------------
    with pd.option_context('display.max_rows', 10, 'display.max_columns', None):
        print(df)
    sys.exit()
    # ------------------------------------------------------------------------------

    arrivals_history_1stop = []

    df['delta'] = df['timestamp'] - df['timestamp'].shift(1)

    for index, row in df.iterrows():
        dict_ins = {}
        dict_ins['stop_id'] = row['stop_id']
        dict_ins['v'] = row['v']
        dict_ins['timestamp'] = row['timestamp']
        dict_ins['delta'] = row['delta']
        arrivals_history_1stop.append(dict_ins)

    return arrivals_history_1stop

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
