# testing lib.Localizer
# -- dump to console
import lib.Localizer as Localizer
import lib.BusAPI as BusAPI
import time, datetime, argparse
from itertools import groupby
import lib.TripDB as TripDB

parser = argparse.ArgumentParser()
parser.add_argument('-r', '--route', dest='route', required=True, help='route number')

args = parser.parse_args()

def localizer_live_singleroute(route):

    # fetch bus positions from NJT API
    bus_data = BusAPI.parse_xml_getBusesForRoute(BusAPI.get_xml_data('nj', 'buses_for_route', route=route))

    # split bus data into groups by direction ['dd']
    key_func = lambda s: s.dd
    bus_data.sort(key=key_func)
    grouped = [list(g) for k, g in groupby(bus_data, key_func)]

    # loop over groups and collect results

    for direction in grouped:

        results = Localizer.infer_stops(position_log=direction, route=route)

        # look up stop names again

        # output results to console
        for index, row in results.iterrows():
            print(
                'bid {bid} dd {dd} lat {lat:f} lon {lon:f} stop_id {stop_id} distance {distance:f}'.format(dd=row.dd, bid=row.bid, lat=row.lat, lon=row.lon, stop_id=row.bcol, distance=row.distance))

    return results

def db_setup(route):

    # date = datetime.datetime.today().strftime('%Y-%m-%d')

    db = TripDB.MySQL('buses', 'buswatcher', 'njtransit', '127.0.0.1', route)
    conn = db.conn
    return conn, db


while True:
    now = datetime.datetime.now()
    localized_positions = localizer_live_singleroute(args.route)
    conn, db = db_setup(args.route)
    db.insert_positions(localized_positions, now)


    time.sleep(15) #make function to sleep for 15 seconds

