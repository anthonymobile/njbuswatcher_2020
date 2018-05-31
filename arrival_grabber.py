# cron-able script that doesn nothing but grab the arrival buses for an entire route of stops
#
#
# call it from CLI:
#
# python arrival_grabber.py -s nj -r 87
#
#
# call it from another script:
#
# from arrival_grabber import fetch_arrivals
# fetch_arrivals(source, route, flag)
# fetch_arrivals('nj', 87, False)
# fetch_arrivals('nj', 87, True) (no fetch, offline testing only)
#

import sqlite3, datetime, sys

import pandas as pd

import argparse
import Buses
import StopsDB


def fetch_arrivals(source, route, flag):

    (conn, db) = db_setup(route)
    stoplist = []

    if flag is False:
        routedata = Buses.parse_route_xml(Buses.get_xml_data(source, 'routes', route=route))
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

    elif flag is True:
        stoplist_query = (
                'SELECT stop_id FROM stop_predictions WHERE rd = %s GROUP BY stop_id;' % route)
        stoplist = pd.read_sql_query(stoplist_query, conn)
        return stoplist

def db_setup(route):
    db = StopsDB.SQLite('data/%s.db' % route)
    conn = sqlite3.connect('data/%s.db' % route)
    return conn, db


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', dest='source', required=True, default='nj', help='source name')
    parser.add_argument('-r', '--route', dest='route', required=True, help='route # ')
    args = parser.parse_args()

    flag = False

    fetch_arrivals(args.source, args.route, flag)

if __name__ == "__main__":
    main()


# TO DO
# 1 rewrite to use mysql
# 2 deploy to webster.hopto.org
