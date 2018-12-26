import pandas as pd
import numpy as np

import geopandas
from scipy.spatial import cKDTree
from shapely.geometry import Point

from . import DataBases

# class TripPosition(BusAPI.KeyValueData):
#
#     def __init__(self,route,run,id,date):
#         KeyValueData.__init__(self)
#         self.route = route
#         self.name = 'trip_position'
#         self.id = ''
#         self.date = datetime.date.today() # autopopulate YYYY-MM-DD on record creation
#         self.timestamp = ''
#         self.run = ''
#         self.stop_id = ''
#         self.dd = ''


# CKDNEAREST
# https://gis.stackexchange.com/questions/222315/geopandas-find-nearest-point-in-other-dataframe
# Here is a helper function that will return the distance and 'Name'
# of the nearest neighbor in gpd2 from each point in gpd1.
# It assumes both gdfs have a geometry column (of points).

def ckdnearest(gdA, gdB, bcol):
    nA = np.array(list(zip(gdA.geometry.x, gdA.geometry.y)) )
    nB = np.array(list(zip(gdB.geometry.x, gdB.geometry.y)) )
    btree = cKDTree(nB)
    dist, idx = btree.query(nA,k=1)
    # using 1 degree = 69 miles = 364,320 feet
    df = pd.DataFrame.from_dict({'distance': (dist.astype(float)*364320),'bcol' : gdB.loc[idx, bcol].values })
    return df

# GET_NEAREST_STOP
#
# Finds the nearest stop, distance to it, from each item in a list of Bus objects.
# Returns as a list of BusPosition objects.
#

def get_nearest_stop(buses):

    # 1. LOAD, FORMAT DATA + CREATE GEODATAFRAME FOR BUS POSITIONS

    #convert Buses into dataframe
    df1 = pd.DataFrame.from_records(buses)
    df1['lat'] = pd.to_numeric(df1['lat'])
    df1['lon'] = pd.to_numeric(df1['lon'])

    # turn the bus positions df1 into a A GeoDataFrame
    # A GeoDataFrame needs a shapely object, so we create a new column Coordinates as a tuple of Longitude and Latitude :
    df1['coordinates'] = list(zip(df1.lon, df1.lat))
    # Then, we transform tuples to Point :
    df1['coordinates'] = df1['coordinates'].apply(Point)
    # Now, we can create the GeoDataFrame by setting geometry with the coordinates created previously.
    gdf1 = geopandas.GeoDataFrame(df1, geometry='coordinates')


    # 2. ACQUIRE STOP LOCATIONS + CREATE GEODATAFRAME
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


    # --------------------------
    # TODO DO DISTANCE CONVERSION PER https://gis.stackexchange.com/questions/279109/calculate-distance-between-a-coordinate-and-a-county-in-geopandas
    # "@anthonymobile If CRS of geodfs are EPSG 4326 (lat/lon) then returned 'dist' will be in degrees. To meters or ft either first convert both gdf to appropriate CRS proj for your location using .to_crs() or convert from degrees as here: https://t.co/FODrAWskNH" / Twitter
    # --------------------------

    # insert inferred_stops back into gdf1
    gdf1=gdf1.join(inferred_stops)


    # AS OF HERE WE HAVE A LIST OF BUSES AND DISTANCES TO NEAREST STOP
    # todo CONVERT TO A BUSPOSITION INSTANCE AND RETURN

    bus_positions=[]
    for index, row in gdf1.iterrows():
        print(row['c1'], row['c2'])
        bus_positions.append(
            DataBases.BusPosition(
                lat =  ,
                lon =  ,
                cars =  ,
                consist = ,
                d =  ,
                dip = ,
                dn =  ,
                fs =  ,
                id =  ,
                m =  ,
                op =  ,
                pd =  ,
                pdRtpiFeedName = ,
                pid =  ,
                rt =  ,
                rtRtpiFeedName =  ,
                rtdd = ,
                rtpiFeedName =  ,
                run =  ,
                wid1 =  ,
                wid2 =  ,
                timestamp = # gdf[0]['timestamp'],

                trip_id =  # TK?,
                stop_id =  # gdf[0]['stop_id'] ???,
                distance_to_stop =  # gdf[0]['distance_to_stop'],
                arrival_flag =

        )

    return bus_positions
