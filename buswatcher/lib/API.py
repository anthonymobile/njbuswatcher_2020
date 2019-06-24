
import json
import geojson
import pandas as pd

import buswatcher.lib.BusAPI as BusAPI
from buswatcher.lib.CommonTools import timeit
from buswatcher.lib.DataBases import SQLAlchemyDBConnection, Trip, BusPosition, ScheduledStop

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
@timeit
def __positions2geojson(df): # todo 2 optimization, less pandas?
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

@timeit
def _fetch_positions_df(route): # todo 2 optimization, less pandas?
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


# positions

def get_positions_byargs(system_map, args, route_descriptions, collection_descriptions):

    if 'rt' in args.keys():
        if args['rt'] == 'all':
            positions_list = pd.DataFrame()
            for r in route_descriptions['routedata']:
                positions_list = positions_list.append(_fetch_positions_df(r['route']))

            return __positions2geojson(positions_list)
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


# get geoJSON
def get_map_layers(system_map, args, route_descriptions, collection_descriptions):
    return system_map.render_geojson(args)

