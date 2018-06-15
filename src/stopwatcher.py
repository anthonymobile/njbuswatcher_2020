# should run as a cron job
# python stopwatcher.py -s nj -r 87

# all this program does is fetch
# the current arrivals for every stop on a source, route
# and stick it in the database

import argparse


def fetch_arrivals(source, route):

    (conn, db) = db_setup(route)

    routedata = Buses.parse_route_xml(Buses.get_xml_data(source, 'routes', route=route))

    stoplist = []

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


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', dest='source', required=True, default='nj', help='source name')
    parser.add_argument('-r', '--route', dest='route', required=True, help='route # ')
    args = parser.parse_args()

    fetch_arrivals(args.source, args.route)

if __name__ == "__main__":
    main()
