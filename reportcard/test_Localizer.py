# testing lib.Localizer
# -- dump to console
import lib.Localizer as Localizer
import lib.BusAPI as BusAPI
import time
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-r', '--route', dest='route', required=True, help='route number')

args = parser.parse_args()

def localizer_live_singleroute(route):

    # test using position_log list input
    bus_data = BusAPI.parse_xml_getBusesForRoute(BusAPI.get_xml_data('nj', 'buses_for_route', route=route))

    results = Localizer.infer_stops(position_log=bus_data, route=route)
    # results.to_html('results.html')

    # loop results to console

    for index, row in results.iterrows():
        print(
            'bid {bid} dd {dd} lat {lat:f} lon {lon:f} stop_id {stop_id} stop_name {stop_name} distance {distance:f}'.format(dd=row.dd, bid=row.bid, lat=row.lat, lon=row.lon, stop_id=row.bcol, distance=row.distance, stop_name=row.st))


while True:
    localizer_live_singleroute(args.route)
    time.sleep(10) #make function to sleep for 10 seconds

