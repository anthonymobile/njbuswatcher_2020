# bus report card v1.0
# May-June 2018

import StopsDB
import Buses
import datetime, sys, sqlite3, argparse
import pandas as pd
import numpy as np
from flask import Flask, render_template


app = Flask(__name__)

@app.route('/<source>/<route>/history')
def getArrivalHistory(source,route):
    stoplist = fetch_arrivals(source,route)
    history = render_arrivals_history_full(source,route,stoplist)

    return render_template('arrivals_history_full.html', history=history)


@app.route('/<source>/<route>/hourly')
def getHourlyHistory(source,route):
    stoplist = fetch_arrivals(source,route)
    hourly = render_arrivals_hourly_mean(source,route,stoplist)

    return render_template('arrivals_history_hourly.html', hourly=hourly)


# @app.route('/<source>/<route>/current')
#
#     delayboard_current(source,route)
#     return render_template('templates/tk????.html', arrivals=arrivals)
#



parser = argparse.ArgumentParser()
parser.add_argument('--nofetch', action='store_true',  help='Do not fetch new arrival predictions load cached data from local db')
args = parser.parse_args()


def db_setup(route):
    db = StopsDB.SQLite('data/%s.db' % route)
    conn = sqlite3.connect('data/%s.db' % route)
    return conn,db

def fetch_arrivals(source,route):
    (conn, db) = db_setup(route)
    stoplist = []
    if args.nofetch is False:
        routedata = Buses.parse_route_xml(Buses.get_xml_data(source, 'routes', route=route))
        for i in routedata.paths:
            for p in i.points:
                if p.__class__.__name__ == 'Stop':
                    stoplist.append(p.identity)
        for s in stoplist:
            arrivals = Buses.parse_stopprediction_xml(Buses.get_xml_data('nj', 'stop_predictions', stop=s, route=route))
            sys.stdout.write('.')
            now = datetime.datetime.now()
            db.insert_positions(arrivals, now)
    elif args.nofetch is True:
        stoplist_query = (
                'SELECT stop_id FROM stop_predictions WHERE rd = %s GROUP BY stop_id;' % route)
        stoplist = pd.read_sql_query(stoplist_query, conn)
    return stoplist.stop_id


def render_arrivals_history_full(source,route,stoplist):

    (conn,db) = db_setup(route)
    arrival_query = ('SELECT * FROM stop_predictions WHERE (rd = %s AND pt = "APPROACHING") ORDER BY stop_id,timestamp;' % route)
    df = pd.read_sql_query(arrival_query, conn)

    df['timestamp'] = df['timestamp'].str.split('.').str.get(0)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp', drop=False)

    arrivals_history_full = []

    for s in stoplist:

        # slice the stop
        df_stop = df.loc[df.stop_id == s]

        # compute interval between this bus and next in log
        df_stop['delta'] = df_stop['timestamp'] - df_stop['timestamp'].shift(1)

        # append it

        for index, row in df_stop.iterrows():
            dict_ins={}
            dict_ins ['stop_id'] =  row['stop_id']
            dict_ins['v'] = row['v']
            dict_ins['timestamp'] = row['timestamp']
            dict_ins['delta'] = row['delta']
            arrivals_history_full.append(dict_ins)

    return arrivals_history_full


def render_arrivals_hourly_mean(source,route,stoplist):

    (conn, db) = db_setup(route)
    arrival_query = (
                'SELECT * FROM stop_predictions WHERE (rd = %s AND pt = "APPROACHING") ORDER BY stop_id,timestamp;' % route)
    df = pd.read_sql_query(arrival_query, conn)

    df['timestamp'] = df['timestamp'].str.split('.').str.get(0)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp', drop=False)

    arrivals_history_hourly = []

    for s in stoplist:

        # slice the stop
        df_stop = df.loc[df.stop_id == s]

        # compute interval between this bus and next in log
        df_stop['delta'] = df_stop['timestamp'] - df_stop['timestamp'].shift(1)

        # resample hourly average

        # need to convert delta to numeric type first per...
        # https://stackoverflow.com/questions/44616546/finding-the-mean-and-standard-deviation-of-a-timedelta-object-in-pandas-df
        df_stop['delta_int'] = df_stop['delta'].values.astype(np.int64)
        df_stop = df_stop.delta_int.resample('H').mean()

        for hour in df_stop.iteritems():
            dict_ins = {}
            dict_ins['hour_top'] = hour[0]
            # dict_ins['stop_id'] = df_stop['stop_id']
            dict_ins['avg_interval'] = hour[1]
            arrivals_history_hourly.append(dict_ins)

    return arrivals_history_hourly

# TO DO

#   CORE FUNCTIONALITY
#   1 ui rendering - first in text, later in graphics. here or in template?

#   NEW FEATURES
#   1   delays (observed travel time) = compare bus at stop n and stop n+5 using vehicle id and stopid and average across last n vehicles?
#   2   schedule adherence = compared observed arrival time against GTFS schedule using run w/ TransitLand API call?

#   PERFORMANCE
#   1   remove redundant code to functions and abstract
#   2   above should write tables out to static files as able, instead of recalc arrivals always (p
#   3


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
