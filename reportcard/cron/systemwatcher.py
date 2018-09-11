# fetches the NJT statewide bus feed
# and dumps it to sqlite, mysql database

import sys
import argparse
import datetime

import reportcard.lib.BusAPI as BusAPI
import reportcard.lib.BusDB as BusDB


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', dest='source', default='nj', help='source name')
    parser.add_argument('--save-raw', dest='raw', default=None, required=False, help='directory to save the raw data to')

    args = parser.parse_args()

    if args.source not in BusAPI._sources:
        print args.source + ' is not a valid source.  Valid sources=' + str(Buses._sources.keys())
        sys.exit(-1)

    db = BusDB.MySQL('buses','buswatcher','njtransit','127.0.0.1')

    now = datetime.datetime.now()
    if args.raw:
        bus_data = BusAPI.parse_xml_getBusesForRouteAll(
            BusAPI.get_xml_data_save_raw(args.source, 'all_buses', args.raw))
    else:
        bus_data = BusAPI.parse_xml_getBusesForRouteAll(BusAPI.get_xml_data(args.source, 'all_buses'))
    db.insert_positions(bus_data, now)

if __name__ == "__main__":
    main()
