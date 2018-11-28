# pulls current bus position data from getBusesForRoute
# 1. calls Localizer.infer_stops to computes distance to nearest stop for each bus
# 2. logs the group to triplog_{route}

import argparse, datetime
from itertools import groupby

import lib.Localizer as Localizer
import lib.BusAPI as BusAPI
import lib.TripsDB as TripsDB


parser = argparse.ArgumentParser()
parser.add_argument('-s', '--source', dest='source', required=True, default='nj', help='source name')
parser.add_argument('-r', '--route', dest='route', required=True, help='route number')
args = parser.parse_args()

def db_setup(route):

    # date = datetime.datetime.today().strftime('%Y-%m-%d')

    db = TripsDB.MySQL('buses', 'buswatcher', 'njtransit', '127.0.0.1', route)
    conn = db.conn
    return conn, db


def main():

    now = datetime.datetime.now()

    # fetch bus positions from NJT API
    bus_data = BusAPI.parse_xml_getBusesForRoute(BusAPI.get_xml_data('nj', 'buses_for_route', route=args.route))

    # split bus data into groups by direction ['dd']
    key_func = lambda s: s.dd
    bus_data.sort(key=key_func)
    nothingburger= [list(g) for k,g in groupby(bus_data, key_func)]

   # loop over groups and collect results

    for direction in nothingburger:

        localized_positions = Localizer.infer_stops(position_log=direction, route=args.route)

        # look up stop names again

        # output results to console
        for index, row in localized_positions.iterrows():
            print(
                'id {id} dd {dd} lat {lat:f} lon {lon:f} stop_id {stop_id} distance {distance} feet'.format(
                    dd=row.dd, id=row.id, lat=row.lat, lon=row.lon, stop_id=row.bcol, distance=int(row.distance)))

    # convert localized_positions to a list of objects of new class TripLogEntry(KeyValueDate)
    #
    # something i can feed the database!!!
    # a class of its own?



    conn, db = db_setup(args.route)
    print ('writing')
    db.insert_positions(localized_positions, now)
    print ('written')

if __name__ == "__main__": main()
