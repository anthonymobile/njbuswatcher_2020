import sys

import geopandas
import pandas as pd
import numpy as np
from scipy.spatial import cKDTree
from shapely.geometry import Point

from . import BusAPI


# using scipy.spatial method in bottom answer here
# https://gis.stackexchange.com/questions/222315/geopandas-find-nearest-point-in-other-dataframe

# USAGE
# todo in production -- called as part of routewatcher.py data acquisition pipeline, and results are written to position log which is now a combined position log and stop log (and deprecates stopwatcher.py)


# https://gis.stackexchange.com/questions/222315/geopandas-find-nearest-point-in-other-dataframe
# Here is a helper function that will return the distance and 'Name' of the nearest neighbor in gpd2 from each point in gpd1. It assumes both gdfs have a geometry column (of points).
def ckdnearest(gdA, gdB, bcol):
    nA = np.array(list(zip(gdA.geometry.x, gdA.geometry.y)) )
    nB = np.array(list(zip(gdB.geometry.x, gdB.geometry.y)) )
    btree = cKDTree(nB)
    dist, idx = btree.query(nA,k=1)
    df = pd.DataFrame.from_dict({'distance': dist.astype(float),'bcol' : gdB.loc[idx, bcol].values })
    return df

def infer_stops(**kwargs):

    # 1. LOAD, FORMAT DATA + CREATE GEODATAFRAME FOR BUS POSITIONS

    # if called with Localizer.infer_stops(position_log=list_of_Bus_objects,route='87')
    #print (kwargs['position_log'])

    if 'position_log' in kwargs:
        # turn the bus objects into a dataframe
        df1 = pd.DataFrame.from_records([bus.to_dict() for bus in kwargs['position_log']])
        df1['lat'] = pd.to_numeric(df1['lat'])
        df1['lon'] = pd.to_numeric(df1['lon'])

        direction = kwargs['position_log'][0].dd
        # print ('bus going to '+ direction)

    elif 'position_log' not in kwargs:
        print('Not supported yet')
        sys.exit()

        # load the whole postiion_log table from buswatcher db into a dataframe like df1 above
        # do something
        # do something
        # do something
        # do something
        # direction = tk

    else:
        print ('insufficient kwargs to Localizer')
        sys.exit()


    # turn the bus positions df1 into a A GeoDataFrame
    # A GeoDataFrame needs a shapely object, so we create a new column Coordinates as a tuple of Longitude and Latitude :
    df1['coordinates'] = list(zip(df1.lon, df1.lat))
    # Then, we transform tuples to Point :
    df1['coordinates'] = df1['coordinates'].apply(Point)
    # Now, we can create the GeoDataFrame by setting geometry with the coordinates created previously.
    gdf1 = geopandas.GeoDataFrame(df1, geometry='coordinates')


    # 2. ACQUIRE DATA + CREATE GEODATAFRAME FOR STOP LOCATIONS

    routedata, a, b, c, d = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data('nj', 'routes', route=kwargs['route']))
    stop_candidates = []

    try:
        for rt in routedata:
            for path in rt.paths:
                if path.d == direction:
                    # print ('match route:' + path.d)
                    for p in path.points:
                        if p.__class__.__name__ == 'Stop':
                            stop_candidates.append({'stop_id':p.identity,'st':p.st,'d':p.d,'lat':p.lat,'lon':p.lon})
                else:
                    pass
    except:
        print('Oops, didnt find the matching route')


    # turn it into a DF
    df2 = pd.DataFrame.from_records(stop_candidates)
    df2['lat'] = pd.to_numeric(df2['lat'])
    df2['lon'] = pd.to_numeric(df2['lon'])

    # A GeoDataFrame needs a shapely object, so we create a new column Coordinates as a tuple of Longitude and Latitude :
    df2['coordinates'] = list(zip(df2.lon, df2.lat))
    # Then, we transform tuples to Point :
    df2['coordinates'] = df2['coordinates'].apply(Point)
    # Now, we can create the GeoDataFrame by setting geometry with the coordinates created previously.
    gdf2 = geopandas.GeoDataFrame(df2, geometry='coordinates')


    # It returns a dataframe with distance and Name columns that you can insert back into gpd1
    inferred_stops = ckdnearest(gdf1, gdf2,'stop_id')

    # insert inferred_stops back into gdf1 and

    gdf1=gdf1.join(inferred_stops)

    # once debugged
    # cull those that are not at stops

    return gdf1
