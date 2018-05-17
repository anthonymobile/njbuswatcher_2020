# bustime NJT v 0.1
# test profile stops
# 31732 (j sq)  20615 (central and manhattan)   30189 (webster and congress)    21853 (willow 19th)

import BusDB
import Buses
import argparse,datetime

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('services', nargs='+', help='Services specified as bus stop#,route# separated by comma with no space')
    args = parser.parse_args()

    db = BusDB.SQLite('data/%s.db' % args.services[0].split(",")[1])

    for service in args.services:
        arrivals = Buses.parse_stopprediction_xml(Buses.get_xml_data('nj', 'stop_predictions', stop=service.split(",")[0], route=service.split(",")[1]))
        now = datetime.datetime.now()
        db.insert_positions(arrivals, now)

if __name__ == "__main__":
    main()
