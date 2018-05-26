# bus report card v1.0
# May-June 2018

import StopsDB
import Buses
import datetime, sys, sqlite3, argparse
import pandas as pd
from flask import Flask

parser = argparse.ArgumentParser()
parser.add_argument('--nofetch', action='store_true',  help='Do not fetch new arrival predictions, '
                                                            'load cached data from local db')
args = parser.parse_args()

app = Flask(__name__)


@app.route('/<source>/<route>')
def delayboard(source,route):

    db = StopsDB.SQLite('data/%s.db' % route)
    stoplist = []

    if args.nofetch is False:
        routedata=Buses.parse_route_xml(Buses.get_xml_data(source,'routes',route=route))


        for i in routedata.paths:
            for p in i.points:
                if p.__class__.__name__== 'Stop':
                    stoplist.append(p.identity)

        for s in stoplist:
            arrivals = Buses.parse_stopprediction_xml(Buses.get_xml_data('nj', 'stop_predictions', stop=s, route=route))
            sys.stdout.write('.')

            now = datetime.datetime.now()
            db.insert_positions(arrivals, now)

    elif args.nofetch is True:
        # build stoplist from the db

        conn = sqlite3.connect('data/%s.db' % route)
        stoplist_query = (
                    'SELECT stop_id FROM stop_predictions WHERE rd = %s GROUP BY stop_id;' % route)
        stoplist = pd.read_sql_query(stoplist_query, conn)

        # print stoplist

        pass

    # A. frequency analysis

    conn = sqlite3.connect('data/%s.db' % route)
    arrival_query = ('SELECT * FROM stop_predictions WHERE (rd = %s AND pt = "APPROACHING") ORDER BY stop_id,timestamp;' % route)
    df = pd.read_sql_query(arrival_query, conn)

    df['timestamp'] = df['timestamp'].str.split('.').str.get(0)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['timestamp_bak'] = df['timestamp']
    df = df.set_index('timestamp')

    frequency_board_full = []
    frequency_board_full.append(['stop_id', 'vehicle', 'time', 'last arrival ago(min)'])

    frequency_board_hrly=[]
    frequency_board_hrly.append(['stop_id','date','hour','avg_freq'])


    for s in stoplist:

        # slice the stop
        df_stop = df.loc[df.stop_id == s]

        # compute interval between this bus and next in log
        df_stop['delta'] = df_stop['timestamp_bak'] - df_stop['timestamp_bak'].shift(1)

        # add it to a frequency_board
        frequency_board_full.append(['stop_id', 'vehicle', 'time', 'last arrival ago(min)'])

        #
        working = [df_stop.stop_id,(df_stop.resample('H').mean('delta'))]

        frequency_board_hrly.append([working['stop_id'], working.index.date, working.index.hour, working['delta']])

    return str(results)

    #
    # ------------------------------------------------------------ PROGRESS ----------------------
    #

    # NEXT = write a summary of the results to a new data file for archiving and only recalc current day or week


    # B. delays (observed travel time) = compare bus at stop n and stop n+5 using vehicle id and stopid and average across last n vehicles?
    # C. schedule adherence = compared observed arrival time against GTFS schedule using run w/ TransitLand API call?


    # 3. render the page = first in text, later in graphics



if __name__ == "__main__":
    app.run(debug=True)
