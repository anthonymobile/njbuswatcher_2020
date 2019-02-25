import json

import lib.BusAPI as BusAPI
from lib.DataBases import DBConfig, SQLAlchemyDBConnection, Trip, BusPosition, ScheduledStop
from sqlalchemy import func
from sqlalchemy.sql.expression import and_

import geojson
import pandas as pd

import datetime

# on-the-fly-GEOJSON-encoder
def positions2geojson(df):
    features = []
    df.apply(lambda X: features.append(
            geojson.Feature(geometry=geojson.Point((X["lon"],
                                                    X["lat"]    )),
                properties=dict(
                                run=X["run"],
                                op=X["op"],
                                dn=X["dn"],
                                pid=X["pid"],
                                dip=X["dip"],
                                id=X["id"],
                                timestamp=X["timestamp"],
                                fs = str(X["fs"]),
                                pd=str(X["pd"])))
                                    )
                                , axis=1)

    return geojson.FeatureCollection(features)

# positions
def get_positions_byargs(args, reportcard_routes):

    positions_dump = []
    if args['rt'] == 'all':
        for r in reportcard_routes:
            waypoints_item = _fetch_positions_json(r['route'])
            positions_dump.append(waypoints_item)
    else:
        waypoints_item = _fetch_positions_json(args['rt'])
        positions_dump.append(waypoints_item)

    return positions_dump

def _fetch_positions_json(route):

    positions = BusAPI.parse_xml_getBusesForRoute(BusAPI.get_xml_data('nj', 'buses_for_route', route=route))
    now = datetime.datetime.now()
    labels = ['bid','lon', 'lat', 'run', 'op', 'dn', 'pid', 'dip', 'id', 'timestamp', 'fs','pd']
    positions_log=pd.DataFrame(columns=labels)

    for bus in positions:
        update = dict()
        for key,value in vars(bus).items():
            if key in labels:
                if key == 'lat' or key == 'lon':
                    value = float(value)
                update[key] = value
        update['timestamp'] = now
        positions_log = positions_log.append(update,ignore_index=True)

    try:
        positions_log = positions_log.set_index('timestamp',drop=False)
    except:
        pass

    positions_geojson = positions2geojson(positions_log)

    return positions_geojson


# get geoJSON for citywide map
def get_map_layers(args, reportcard_routes):

    # if we only want a single stop geojson
    if 'stop_id' in args.keys():

        # query the db and grab the lat lon for the first record that stop_id matches this one
        with SQLAlchemyDBConnection(DBConfig.conn_str) as db:
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
