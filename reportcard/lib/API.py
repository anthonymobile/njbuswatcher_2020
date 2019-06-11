
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
def get_positions_byargs(args, route_definitions, collection_descriptions):

    if 'rt' in args.keys():
        if args['rt'] == 'all':
            positions_list = pd.DataFrame()
            for r in route_definitions:
                positions_list = positions_list.append(_fetch_positions_df(r['route']))
                # positions_list.append(positions_df)
            return positions2geojson(positions_list)
        else:
            return positions2geojson(_fetch_positions_df(args['rt']))

    elif 'collection' in args.keys():
        positions_list = pd.DataFrame()
        for city in collection_descriptions:
            if args['collection'] == city['collection']:
                # iterate over its routelist
                for r in city['routelist']:
                    positions_list = positions_list.append(_fetch_positions_df(r))
                    # positions_list.append(positions_df)
                return positions2geojson(positions_list)


def _fetch_positions_df(route):
    positions = BusAPI.parse_xml_getBusesForRoute(BusAPI.get_xml_data('nj', 'buses_for_route', route=route))
    labels = ['bid', 'lon', 'lat', 'run', 'op', 'dn', 'pid', 'dip', 'id', 'fs', 'pd']
    positions_log=pd.DataFrame(columns=labels)
    for bus in positions:
        update = dict()
        for key,value in vars(bus).items():
            if key in labels:
                if key == 'lat' or key == 'lon':
                    value = float(value)
                update[key] = value
        positions_log = positions_log.append(update,ignore_index=True)
    try:
        positions_log = positions_log.set_index('timestamp',drop=False)
    except:
        pass
    return positions_log # returns a dataframe


# get geoJSON for citywide map
def get_map_layers(args, route_definitions,collection_descriptions):
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
            # format for geojson
            stop_coordinates = [float(stop_query[1]), float(stop_query[2])]
            stop_geojson = geojson.Point(stop_coordinates)
            # return stop_lnglatlike, stop_geojson
            return stop_geojson

    # otherwise continue to get waypoints/stops for all routes, one route
    elif 'rt' in args.keys():
        waypoints = []
        stops = []
        if args['rt'] == 'all':
            for r in route_definitions:
                waypoints_item, stops_item = _fetch_layers_json(r['route'])
                waypoints.append(waypoints_item)
                stops.append(stops_item)
        else:
            waypoints_item, stops_item = _fetch_layers_json(args['rt'])
            waypoints.append(waypoints_item)
            stops.append(stops_item)

    # or a collection of routes
    elif 'collection' in args.keys():
        waypoints = []
        stops = []
        # pick the right collection
        for c in collection_descriptions:
            if c['collection_url'] == args['collection']:
                for r in c['routelist']:
                    waypoints_item, stops_item = _fetch_layers_json(r)
                    waypoints.append(waypoints_item)
                    stops.append(stops_item)

    # now render the layers as geojson
    if args['layer']=='waypoints':
        waypoints_featurecollection = geojson.FeatureCollection(waypoints)
        return waypoints_featurecollection
    elif args['layer']=='stops':
        stops_featurecollection = geojson.FeatureCollection(stops)
        return stops_featurecollection

def _fetch_layers_json(route):
    routes, coordinate_bundle = BusAPI.parse_xml_getRoutePoints(
        BusAPI.get_xml_data('nj', 'routes', route=route))
    waypoints_feature = json.loads(coordinate_bundle['waypoints_geojson'])
    waypoints_feature = geojson.Feature(geometry=waypoints_feature)
    stops_feature = json.loads(coordinate_bundle['stops_geojson'])
    stops_feature = geojson.Feature(geometry=stops_feature)
    return waypoints_feature, stops_feature
