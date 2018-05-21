# bustime NJT v 0.1

import sys
import StopsDB
import Buses
import argparse,datetime

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', dest='source', default='nj', help='source name')
    parser.add_argument('-r', '--route', dest='route', required=True, help='Route number')
    args = parser.parse_args()

    db = StopsDB.SQLite('data/%s.db' % args.route)

    #
    # grab list of stops on this route from NJT API
    #
    # use the Route class in Buses.py to parse the http://mybusnow.njtransit.com/bustime/map/getRoutePoints.jsp?route=119 method

    routedata=Buses.parse_route_xml(Buses.get_xml_data(args.source,'routes',route=args.route))

    # now have to extract only the Buses.Stop instances (Stop.st = stop_id)  from the "Path points" attrib into Stoplist

    # print dir(routedata)
    # print dir(routedata.Stop)
    # print dir(routedata.paths)
    stoplist=[]
    for i in routedata.paths: # just 1 item
        for p in i.points:
            if p.__class__.__name__== 'Stop':
                stoplist.append(p.identity)
                print p.identity

    #
    # and iterate grabbing all arrivals for all of those stops
    #
    for s in stoplist:
        arrivals = Buses.parse_stopprediction_xml(
            Buses.get_xml_data('nj', 'stop_predictions', stop=s, route=args.route))
        print arrivals
        now = datetime.datetime.now()
        db.insert_positions(arrivals, now)


if __name__ == "__main__":
    main()
