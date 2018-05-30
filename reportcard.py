# bus report card v1.0
# May-June 2018


import argparse

import pandas as pd
import numpy as np
from flask import Flask, render_template

from arrival_grabber import fetch_arrivals, db_setup

app = Flask(__name__)


@app.route('/<source>/<route>/history')
def getArrivalHistory(source, route):
    stoplist = fetch_arrivals(source, route, args.nofetch)
    history = render_arrivals_history_full(source, route, stoplist)
    return render_template('arrivals_history_full.html', history=history)


@app.route('/<source>/<route>/hourly')
def getHourlyHistory(source, route):
    stoplist = fetch_arrivals(source, route, args.nofetch)
    hourly = render_arrivals_hourly_mean(source, route, stoplist)
    return render_template('arrivals_history_hourly.html', hourly=hourly)

# deprecate the nofetch, this script should never fetch data
# that should be a separately provisioned cron-controlled process
#
parser = argparse.ArgumentParser()
parser.add_argument('--nofetch', action='store_true',
                     help='Do not fetch new arrival predictions load cached data from local db')
args = parser.parse_args()


def timestamp_fix(data):
    data['timestamp'] = data['timestamp'].str.split('.').str.get(0)
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    data = data.set_index('timestamp', drop=False)

    return data


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


# TO DO

#   CORE FUNCTIONALITY
#   1 ui rendering - first in text, later in graphics. here or in template?
#   2 render a matplotlib histogram for the hourly, and show it in teh webpage the top of the table

#   NEW FEATURES
#   1   delays (observed travel time) = compare bus at stop n and stop n+5 using vehicle id and stopid and average across last n vehicles?
#   2   schedule adherence = compared observed arrival time against GTFS schedule using run w/ TransitLand API call?

#   PERFORMANCE
#   1   remove redundant code to functions and abstract
#   2   above should write tables out to static files as able, instead of recalc arrivals always (p
#   3


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
