# bus report card v1.0
# May-June 2018

import StopsDB
import Buses
import datetime, sys, sqlite3, argparse
import pandas as pd
import jsonify, json
from flask import Flask



app = Flask(__name__)

@app.route('/<source>/<route>')
def getArrivalHistory(source,route):
    stoplist = fetch_arrivals(source,route)
    results = delayboard_history(source,route,stoplist)
    return results

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


def delayboard_history(source,route,stoplist):
    (conn,db) = db_setup(route)
    arrival_query = ('SELECT * FROM stop_predictions WHERE (rd = %s AND pt = "APPROACHING") ORDER BY stop_id,timestamp;' % route)
    df = pd.read_sql_query(arrival_query, conn)


    df['timestamp'] = df['timestamp'].str.split('.').str.get(0)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['timestamp_bak'] = df['timestamp']
    df = df.set_index('timestamp')

    delayboard_history = []
    delayboard_history.append(['stop_id', 'vehicle', 'time', 'last arrival ago(min)'])

    for s in stoplist:

        # slice the stop
        df_stop = df.loc[df.stop_id == s]

        # compute interval between this bus and next in log
        df_stop['delta'] = df_stop['timestamp_bak'] - df_stop['timestamp_bak'].shift(1)

        # add it to a frequency_board
        delayboard_history.append([df_stop['stop_id'], df_stop['v'], df_stop['delta']])

        # jsonify and return
        jsonStr = json.dumps(delayboard_history)

    return jsonify(Arrivals=jsonStr)





# @app.route('/<source>/<route>/history')
#     delayboard_history(source,route)
#     return render_template('templates/tk????.html', arrivals=arrivals)

# @app.route('/<source>/<route>/history')
#     delayboard_history(source,route)
#     return render_template('templates/tk????.html', arrivals=arrivals)
#
# @app.route('/<source>/<route>/current')
#
#     delayboard_current(source,route)
#     return render_template('templates/tk????.html', arrivals=arrivals)
#
# @app.route('<source>/<route>/hourly')
#
#     delayboard_hourly(source,route)
#     return render_template('templates/tk????.html', arrivals=arrivals)



        # working = [df_stop.stop_id,(df_stop.resample('H').mean('delta'))]
        # frequency_board_hrly.append([working['stop_id'], working.index.date, working.index.hour, working['delta']])


    # NEXT = write a summary of the results to a new data file for archiving and only recalc current day or week

    # open(('data/frequency_board_hrly_%s.txt' % route),w)



    # B. delays (observed travel time) = compare bus at stop n and stop n+5 using vehicle id and stopid and average across last n vehicles?
    # C. schedule adherence = compared observed arrival time against GTFS schedule using run w/ TransitLand API call?


    # 3. render the page = first in text, later in graphics



if __name__ == "__main__":
    app.run(debug=True)
