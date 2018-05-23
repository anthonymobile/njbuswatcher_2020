# bus report card v1.0
# May-June 2018

import StopsDB
import Buses
import datetime, argparse, sys, sqlite3
import pandas as pd
from flask import Flask


app = Flask(__name__)

def delayboard(source,route):

    # parser = argparse.ArgumentParser()
    # parser.add_argument('-s', '--source', dest='source', default='nj', help='source name')
    # parser.add_argument('-r', '--route', dest='route', required=True, help='Route number')
    # args = parser.parse_args()

    db = StopsDB.SQLite('data/%s.db' % route)

    # grab list of all stops on this route from NJT API
    routedata=Buses.parse_route_xml(Buses.get_xml_data(source,'routes',route=route))
    stoplist=[]
    for i in routedata.paths: # just 1 item
        for p in i.points:
            if p.__class__.__name__== 'Stop':
                stoplist.append(p.identity)

    # grab all current arrival predictions for all stops on the route and log to db
    sys.stdout.write('Fetching arrival predictions')
    for s in stoplist:
        arrivals = Buses.parse_stopprediction_xml(
            Buses.get_xml_data('nj', 'stop_predictions', stop=s, route=route))

        sys.stdout.write('.')
        now = datetime.datetime.now()
        db.insert_positions(arrivals, now)

    # from all time, copy observations of 'approaching'(e.g. 0-1? min ETA) buses into a data frame, sorted by stop and time
    conn = sqlite3.connect('data/%s.db' % route)
    arrival_query = ('SELECT * FROM stop_predictions WHERE (rd = %s AND pt = "APPROACHING") ORDER BY stop_id,timestamp;' % route)
    df = pd.read_sql_query(arrival_query, conn)

    # A. frequency analysis

    # prepare timestamp - trim, convert, and index
    df['timestamp'] = df['timestamp'].str.split('.').str.get(0)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp')


    for s in stoplist:

        # slice the stop
        df_stop = df.loc[df.stop_id == s]

        # calculate the time difference
        df_stop['delta'] = df_stop.timestamp - df_stop.timestamp.shift(1)
        print df_stop['delta']

        # calculate average delay by hour

        hourly_average = df_stop['delta'].resample('H').mean()
        print hourly_average

    sys.exit()

    #
    # ------------------------------------------------------------ PROGRESS ----------------------
    #

    # NEXT
    # write a summary of the results
    # to a new data file for archiving
    # and only recalc current day or week


    # B. delays (observed travel time)
    # compare bus at stop n and stop n+5 using vehicle id and stopid
    # average across last n vehicles?

    # C. schedule adherence
    # compared observed arrival time against GTFS schedule using run #
    # TransitLand API call?


    # 3. render the page
    # first in text, later in graphics


# after https://www.youtube.com/watch?v=QJtWxm12Eo0
@app.route('/<source>/<route>')
def hello_world(source,route):
    delayboard(source,route) # call the mainroutine, not sure what goes into it
    return webpages

if __name__ == "__main__":
    app.run(debug=True)
