# bus report card v1.0
# May-June 2018

import StopsDB
import Buses
import datetime, argparse, sys, sqlite3
import pandas as pd
from flask import Flask


app = Flask(__name__)

def delayboard(source,route):


    db = StopsDB.SQLite('data/%s.db' % route)
    routedata=Buses.parse_route_xml(Buses.get_xml_data(source,'routes',route=route))
    stoplist=[]

    for i in routedata.paths:
        for p in i.points:
            if p.__class__.__name__== 'Stop':
                stoplist.append(p.identity)

    for s in stoplist:
        arrivals = Buses.parse_stopprediction_xml(
            Buses.get_xml_data('nj', 'stop_predictions', stop=s, route=route))

        now = datetime.datetime.now()
        db.insert_positions(arrivals, now)

    # A. frequency analysis

    conn = sqlite3.connect('data/%s.db' % route)
    arrival_query = ('SELECT * FROM stop_predictions WHERE (rd = %s AND pt = "APPROACHING") ORDER BY stop_id,timestamp;' % route)
    df = pd.read_sql_query(arrival_query, conn)

    df['timestamp'] = df['timestamp'].str.split('.').str.get(0)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp')

    results=[]
    results.append(['stop_id','hourly_delay'])
    for s in stoplist:

        # slice the stop
        df_stop = df.loc[df.stop_id == s]

        # calculate the time difference
        df_stop['delta'] = df_stop['timestamp'] - df_stop['timestamp'].shift(1)

        # calculate average delay by hour
        results.append([df.stop_id,(df_stop.delta.resample('H').mean())])

    return results

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

    return delayboard(source,route) # call the mainroutine, not sure what goes into it

if __name__ == "__main__":
    app.run(debug=True)
