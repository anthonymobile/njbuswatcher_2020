# bustime NJT v 0.1

import StopsDB
import Buses
import datetime, argparse, sys, sqlite3
import pandas as pd
from operator import itemgetter


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
    sys.stdout.write('Fetching arrival predictions')
    for s in stoplist:
        arrivals = Buses.parse_stopprediction_xml(
            Buses.get_xml_data('nj', 'stop_predictions', stop=s, route=args.route))

        sys.stdout.write('.')
        now = datetime.datetime.now()
        db.insert_positions(arrivals, now)

    # from all time, copy observations of 'approaching'(e.g. 0-1? min ETA) buses into a data frame, sorted by stop and time
    conn = sqlite3.connect('data/%s.db' % args.route)
    arrival_query = ('SELECT * FROM stop_predictions WHERE (rd = %s AND pt = "APPROACHING") ORDER BY stop_id,timestamp;' % args.route)
    df = pd.read_sql_query(arrival_query, conn)

    # A. frequency analysis

    # prepare timestamp - trim, convert, and index
    df['timestamp'] = df['timestamp'].str.split('.').str.get(0)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp')


    for s in stoplist:
        try:
            # slice the stop
            df_stop = df.loc[df.stop_id == s]

            # calculate timedelta between each row in seconds
            # https://stackoverflow.com/questions/16777570/calculate-time-difference-between-pandas-dataframe-indices
            def delay(arrivaltime):
                = (df_stop['timestamp'] - df_stop['timestamp'].shift()).fillna(0)
                return delta
            df_stop['delta'].apply(delay)

            # print list of delay values
            print (df_stop['delta'])

            # calculate average delay by hour
            # add a sorting?
            delay_histogram = df_stop.groupby(df_stop.timestamp.hour).mean(df_stop['delta'])

            #
            # ------------------------------------------------------------ PROGRESS ----------------------
            #

        except KeyError:
            print ('Stop %s has no arrivals in the log, log probably incomplete.' % s)
            pass

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
