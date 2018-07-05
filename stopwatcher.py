# should run as a cron job
# python stopwatcher.py -s nj -r 87

# all this program does is fetch
# the current arrivals for every stop on a source, route
# and stick it in the database

import src.BusAPI as Buses
from src.reportcard_helpers import *

import argparse, sys, datetime


def fetch_arrivals(source, route):

    (conn, db) = db_setup(route)

    routedata = Buses.parse_xml_getRoutePoints(Buses.get_xml_data(source, 'routes', route=route))

    stoplist = []

    for rt in routedata:
        for path in rt.paths:
            for p in path.points:
                if p.__class__.__name__ == 'Stop':
                    stoplist.append(p.identity)

    for s in stoplist:
        arrivals = Buses.parse_xml_getStopPredictions(Buses.get_xml_data('nj', 'stop_predictions', stop=s, route=route))
        # sys.stdout.write('.')
        now = datetime.datetime.now()
        db.insert_positions(arrivals, now)

    return


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', dest='source', required=True, default='nj', help='source name')
    parser.add_argument('-r', '--route', dest='route', required=True, help='route # ')
    args = parser.parse_args()

    fetch_arrivals(args.source, args.route)

if __name__ == "__main__":
    main()
