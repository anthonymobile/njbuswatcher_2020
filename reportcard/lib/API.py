# todo rewrite positions calls to accept a collection not just a single route as an argument
# e.g. figure out how to pass through the list of route #s and then fetch and concatenate the individual route geojsons (probably write another API call, easier to do in python than JS?)



import json
import geojson
import pandas as pd

import lib.BusAPI as BusAPI
from lib.DataBases import SQLAlchemyDBConnection, Trip, BusPosition, ScheduledStop
# from sqlalchemy import func
# from sqlalchemy.sql.expression import and_

# concatenate a list of geojson featurecollections into 1 -- per https://github.com/batpad/merge-geojson
def fc_concat(fc_list):
    fc = {
        'type': 'FeatureCollection',
        'features': []
    }
    text = str(fc_list)
    for line in text.splitlines():
        obj = json.loads(line)
        fc['features'].extend(obj['features'])
    return fc

# on-the-fly-GEOJSON-encoder
def positions2geojson(df):
    features = []
    df.apply(lambda X: features.append(
            geojson.Feature(geometry=geojson.Point((X["lon"],
                                                    X["lat"]    )),
                # properties=dict(
                #                 run=X["run"],
                #                 op=X["op"],
                #                 dn=X["dn"],
                #                 pid=X["pid"],
                #                 dip=X["dip"],
                #                 id=X["id"],
                #                 timestamp=X["timestamp"],
                #                 fs = str(X["fs"]),
                #                 pd=str(X["pd"])))
                #                     )
                #                 , axis=1)
                properties = dict(
                    run=X["run"],
                    op=X["op"],
                    dn=X["dn"],
                    pid=X["pid"],
                    dip=X["dip"],
                    id=X["id"],
                    fs=str(X["fs"]),
                    pd=str(X["pd"])))
                )
                , axis = 1)

    return geojson.FeatureCollection(features)

# positions
def get_positions_byargs(args, reportcard_routes):
    if args['rt'] == 'all':
        positions_list = pd.DataFrame()
        for r in reportcard_routes:
            positions_list = positions_list.append(_fetch_positions_df(r['route']))
            # positions_list.append(positions_df)
        positions_geojson=positions2geojson(positions_list)
    else:
        positions_geojson = positions2geojson(_fetch_positions_df(args['rt']))
    return positions_geojson

def _fetch_positions_df(route):

    positions = BusAPI.parse_xml_getBusesForRoute(BusAPI.get_xml_data('nj', 'buses_for_route', route=route))
    # now = datetime.now()
    # labels = ['bid','lon', 'lat', 'run', 'op', 'dn', 'pid', 'dip', 'id', 'timestamp', 'fs','pd']
    labels = ['bid', 'lon', 'lat', 'run', 'op', 'dn', 'pid', 'dip', 'id', 'fs', 'pd']
    positions_log=pd.DataFrame(columns=labels)

    for bus in positions:
        update = dict()
        for key,value in vars(bus).items():
            if key in labels:
                if key == 'lat' or key == 'lon':
                    value = float(value)
                update[key] = value
        # update['timestamp'] = now
        positions_log = positions_log.append(update,ignore_index=True)

    try:
        positions_log = positions_log.set_index('timestamp',drop=False)
    except:
        pass

    return positions_log # returns a dataframe


# get geoJSON for citywide map
def get_map_layers(args, reportcard_routes):

    # if we only want a single stop geojson
    if 'stop_id' in args.keys():

        # query the db and grab the lat lon for the first record that stop_id matches this one
        with SQLAlchemyDBConnection() as db:
            stop_query = db.session.query(
                ScheduledStop.stop_id,
                ScheduledStop.lat,
                ScheduledStop.lon) \
                .filter(ScheduledStop.stop_id == args['stop_id']) \
                .first()

            # format for mapbox LngLatLike
            # stop_lnglatlike = [float(stop_query[2]), float(stop_query[1])]

            # format for geojson
            stop_coordinates = [float(stop_query[1]), float(stop_query[2])]
            stop_geojson = geojson.Point(stop_coordinates)

            # return stop_lnglatlike, stop_geojson
            return stop_geojson

    # otherwise continue to get waypoints/stops for one or more routes
    waypoints = []
    stops = []

    if args['rt'] == 'all':
        for r in reportcard_routes:
            waypoints_item, stops_item = _fetch_layers_json(r['route'])
            waypoints.append(waypoints_item)
            stops.append(stops_item)
    else:
        waypoints_item, stops_item = _fetch_layers_json(args['rt'])
        waypoints.append(waypoints_item)
        stops.append(stops_item)

    if args['layer']=='waypoints':
        waypoints_featurecollection = geojson.FeatureCollection(waypoints)
        return waypoints_featurecollection
    elif args['layer']=='stops':
        stops_featurecollection = geojson.FeatureCollection(stops)
        return stops_featurecollection

def _fetch_layers_json(route):
    routes, coordinate_bundle = BusAPI.parse_xml_getRoutePoints(
        BusAPI.get_xml_data('nj', 'routes', route=route))

    # todo collapse these into...
    waypoints_feature = json.loads(coordinate_bundle['waypoints_geojson'])
    waypoints_feature = geojson.Feature(geometry=waypoints_feature)
    stops_feature = json.loads(coordinate_bundle['stops_geojson'])
    stops_feature = geojson.Feature(geometry=stops_feature)

    # todo this?
    # waypoints_feature = geojson.Feature(geometry=json.loads(coordinate_bundle['waypoints_geojson']))
    # stops_feature = geojson.Feature(geometry=json.loads(coordinate_bundle['stops_geojson']))

    return waypoints_feature, stops_feature
