# fetches the NJT bus locations for all buses currently on a source, route and dumps it to mysql database using a table for that line
# usage python routewatcher.py -s nj -r 87

import sys
import argparse
import datetime

import lib.BusAPI as BusAPI
import lib.BusRouteLogsDB as BusRouteLogsDB

def db_setup(route):
    db = BusRouteLogsDB.MySQL('buses', 'buswatcher', 'njtransit', '127.0.0.1', route)
    conn = db.conn
    return conn, db


def fetch_locations(source, route):

    (conn,db) = db_setup(route)

    bus_data = BusAPI.parse_xml_getBusesForRoute(BusAPI.get_xml_data(source, 'buses_for_route',route=route))

    now = datetime.datetime.now()
    db.insert_positions(bus_data, now)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', dest='source', default='nj', help='source name')
    parser.add_argument('-r', '--route', dest='route', required=True, help='route number')

    args = parser.parse_args()

    if args.source not in BusAPI._sources:
        print args.source + ' is not a valid source.  Valid sources=' + str(BusAPI._sources.keys())
        sys.exit(-1)

    fetch_locations(args.source, args.route)


if __name__ == "__main__":
    main()
