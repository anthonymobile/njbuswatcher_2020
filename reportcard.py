# bustime NJT v 0.1

import StopsDB
import Buses
import datetime
import argparse
import pandas as pd
import sqlite3

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', dest='source', default='nj', help='source name')
    parser.add_argument('-r', '--route', dest='route', required=True, help='Route number')
    args = parser.parse_args()

    db = StopsDB.SQLite('data/%s.db' % args.route)

    # grab list of all stops on this route from NJT API
    routedata=Buses.parse_route_xml(Buses.get_xml_data(args.source,'routes',route=args.route))
    stoplist=[]
    for i in routedata.paths: # just 1 item
        for p in i.points:
            if p.__class__.__name__== 'Stop':
                stoplist.append(p.identity)

    # grab all current arrival predictions for all stops on the route and log to db
    for s in stoplist:
        arrivals = Buses.parse_stopprediction_xml(
            Buses.get_xml_data('nj', 'stop_predictions', stop=s, route=args.route))
        # print arrivals
        now = datetime.datetime.now()
        db.insert_positions(arrivals, now)

    # from all time, copy observations of 'approaching'(e.g. 0-1? min ETA) buses into a data frame, sorted by stop and time
    conn = sqlite3.connect('data/%s.db' % args.route)
    arrival_query = ('SELECT * FROM stop_predictions WHERE (rd = %s AND pt = "APPROACHING") ORDER BY stop_id,timestamp;' % args.route)
    df = pd.read_sql_query(arrival_query, conn)
    # print("bus id,stop id,arrival prediction,timestamp")
    # print df[['v','stop_id','pt','timestamp']]

    #
    # ------------------------------------------------------------ PROGRESS ----------------------
    #

    # 1. Frequency of service analysis. This is simply calculated by looking at how often a bus on a particular route passes a given stop.
    # this route does it for all stops on the route, later should do it for specified stops
    # create list of only observations of buses arriving at stops
    # calculate the mean time between arrivals for various periods (last hour, last day, last week, rush hour only, etc)
    # for stop in stop_id:    # not sure if this is how to do it, do i need to unique(stop_id) or something)
        # for a given stop
        # find all the buses in the desired time window
        # sort the buses by timestamp
        # calculate the time in minutes between them
        # average over the # of buses
    # q: what happens when there are gaps in the data? can detect this?


    # 2. Travel time analysis. How long is it taking to get
    # to the next. We can do this by tracking individual vehicles and seeing how long it takes them to get
    # to the next.
    # is there a unique run id? for each date, calculate travel time on each segment of the route and display average for all buses?
    #
    #

    # 3. render the page

    # first in text, later in graphics

    # 4. render the route

    # app = Flask(__name__)
    # api = Api(app)
    # @app.route('/<path:path>')
    # def staticHost(self, path):
    #     try:
    #         return flask.send_from_directory(app.config['RESULT_STATIC_PATH'], path)
    #     except werkzeug.exceptions.NotFound as e:
    #         if path.endswith("/"):
    #             return flask.send_from_directory(app.config['RESULT_STATIC_PATH'], path + "index.html")
    #         raise e



if __name__ == "__main__":
    main()
