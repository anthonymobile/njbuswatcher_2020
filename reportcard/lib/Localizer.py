import geopandas
import pandas as pd
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
    df = pd.DataFrame.from_dict({'distance': dist.astype(int),'bcol' : gdB.loc[idx, bcol].values })
    return df

def infer_stops(position_list,route):

    # FORMAT DATA + CREATE GEODATAFRAME FOR POSITIONS

    # turn the bus objects into a dataframe
    df1 = pd.DataFrame.from_records([bus.to_dict() for bus in position_list])
    df1['lat'] = pd.to_numeric(df1['lat'])
    df1['lon'] = pd.to_numeric(df1['lon'])

    # A GeoDataFrame needs a shapely object, so we create a new column Coordinates as a tuple of Longitude and Latitude :
    df1['coordinates'] = list(zip(df1.lon, df1.lat))
    # Then, we transform tuples to Point :
    df1['coordinates'] = df1['coordinates'].apply(Point)
    # Now, we can create the GeoDataFrame by setting geometry with the coordinates created previously.
    gdf1 = geopandas.GeoDataFrame(df1, geometry='coordinates')

#
#
#
#
# SPLIT DF1 BY 'd'
# THEN DO THE BELOW FOR EACH SUBGROUP
# SO THAT EACH SUBGROUP GETS LOCALIZED BASED ON
# THE STOPLIST THAT IS SUITABLE FOR ITS DIRECTION
#
#
#
#


    # ACQUIRE DATA + CREATE GEODATAFRAME FOR STOPS

    routedata, a, b, waypoints_geojson, stops_geojson = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data('nj', 'routes', route=route))
    route_stop_list = []

    for rt in routedata:
        for path in rt.paths:
            for p in path.points:
                if p.__class__.__name__ == 'Stop':
                    route_stop_list.append(p.identity)

    # find the one for the service and direction we're on,
    # by matching headsigns against the first vehicle in our
    # current position log

    try:
        for route in route_stop_list:
            # if 'd' from route_stop_list = headsign
            if route['d'] == position_list[0]['d']:
                stoplist_match = route
            else:
                pass
    except stoplist_match is False:
        print('Oops, didnt find the matching route')
        breakpoint()



    # turn it into a DF
    df2 = pd.DataFrame.from_records(stoplist_match)

    # A GeoDataFrame needs a shapely object, so we create a new column Coordinates as a tuple of Longitude and Latitude :
    df2['coordinates'] = list(zip(df.lon, df.lap))
    # Then, we transform tuples to Point :
    df2['coordinates'] = df['coordinates'].apply(Point)
    # Now, we can create the GeoDataFrame by setting geometry with the coordinates created previously.
    gdf2 = geopandas.GeoDataFrame(df2, geometry='coordinates')


    # It returns a dataframe with distance and Name columns that you can insert back into gpd1
    inferred_stops = ckdnearest(gdf1, gdf2,'stop_id')

    # once debugged
    # cull those that are not at stops

    return inferred_stops
