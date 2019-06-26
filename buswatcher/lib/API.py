
import json
import geojson
import pandas as pd

import buswatcher.lib.BusAPI as BusAPI
from buswatcher.lib.CommonTools import timeit
from buswatcher.lib.DataBases import SQLAlchemyDBConnection, Trip, BusPosition, ScheduledStop
from sqlalchemy import func, text


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
def __positions2geojson(df): # future: optimization, less pandas, 0.2 seconds per run
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

# @timeit
def _fetch_positions_df(route): # future: optimization, less pandas? (each route takes 0.1 to 0.2 seconds, kills the statewide map... maybe process that with its own process on a single buses_all df)
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


def current_buspositions_from_db_for_index():

    with SQLAlchemyDBConnection() as db:
        query = db.session.query(BusPosition).filter(BusPosition.timestamp >= func.ADDDATE(func.CURRENT_TIMESTAMP(), text('interval -1 minute'))).all()
        positions = query
        positions_list=[]
        for bus in positions:
            positions_list.append(
                {
                    'lon':bus.lon,
                    'lat':bus.lat,
                    'run':bus.run,
                    'op':bus.op,
                    'dn':bus.dn,
                    'pid':bus.pid,
                    'id': bus.id,
                    'fs': bus.fs,
                    'pd': bus.pd,
                    'rt': bus.rt
                }

            )
        # positions_features = []

        f = lambda X: geojson.Feature(geometry=geojson.Point((float(X["lon"]),float(X["lat"])),
                            properties=dict(
                                run=X["run"],
                                op=X["op"],
                                dn=X["dn"],
                                pid=X["pid"],
                                id=X["id"],
                                fs=str(X["fs"]),
                                pd=str(X["pd"]))
        ))

        positions_features = [f(X) for X in positions_list]

        route_count = len(list(set([v['rt'] for v in positions_list])))

        return geojson.FeatureCollection(positions_features),len(positions_list), route_count


# positions

def get_positions_byargs(system_map, args, route_descriptions, collection_descriptions):

    if 'rt' in args.keys():
        if args['rt'] == 'all':

            return current_buspositions_from_db_for_index()[0] # just send the feature collection back
        else:
            return __positions2geojson(_fetch_positions_df(args['rt']))

    elif 'collection' in args.keys():
        positions_list = pd.DataFrame()
        for city,citydata in collection_descriptions.items():
            if args['collection'] == citydata['collection']:
                # iterate over its routelist
                for r in citydata['routelist']:
                    positions_list = positions_list.append(_fetch_positions_df(r))
                    # positions_list.append(positions_df)
                return __positions2geojson(positions_list)




