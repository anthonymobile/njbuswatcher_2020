import sys, datetime

import geopandas
import pandas as pd
import numpy as np
from scipy.spatial import cKDTree
from shapely.geometry import Point

from . import BusAPI


class TripPosition(BusAPI.KeyValueData):

    def __init__(self,route,run,id,date):
        KeyValueData.__init__(self)
        self.route = route
        self.name = 'trip_position'
        self.id = ''
        self.date = datetime.date.today() # autopopulate YYYY-MM-DD on record creation
        self.timestamp = ''
        self.run = ''
        self.stop_id = ''
        self.dd = ''

# using scipy.spatial method in bottom answer here
# https://gis.stackexchange.com/questions/222315/geopandas-find-nearest-point-in-other-dataframe


# https://gis.stackexchange.com/questions/222315/geopandas-find-nearest-point-in-other-dataframe
# Here is a helper function that will return the distance and 'Name' of the nearest neighbor in gpd2 from each point in gpd1. It assumes both gdfs have a geometry column (of points).
def ckdnearest(gdA, gdB, bcol):
    nA = np.array(list(zip(gdA.geometry.x, gdA.geometry.y)) )
    nB = np.array(list(zip(gdB.geometry.x, gdB.geometry.y)) )
    btree = cKDTree(nB)
    dist, idx = btree.query(nA,k=1)
    # using 1 degree = 69 miles = 364,320 feet
    df = pd.DataFrame.from_dict({'distance': (dist.astype(float)*364320),'bcol' : gdB.loc[idx, bcol].values })
    return df

def infer_stops(**kwargs):

    # - Sort position  records by direction(‘dd’)
    # - Run  them through stop_imputer
    # - Create or add  a  Call or PositionReport  to  a
    # Trip object that has unique ID  for date and run_id

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

    # # --------------------------
    # # TODO DO DISTANCE CONVERSION PER https://gis.stackexchange.com/questions/279109/calculate-distance-between-a-coordinate-and-a-county-in-geopandas
    #
    # # "@anthonymobile If CRS of geodfs are EPSG 4326 (lat/lon) then returned 'dist' will be in degrees. To meters or ft either first convert both gdf to appropriate CRS proj for your location using .to_crs() or convert from degrees as here: https://t.co/FODrAWskNH" / Twitter
    #
    #
    # #--------------------------
    # # TODO CONVERT GDF1 TO A LIST OF TripPosition OBJECTS
    #
    # something = 0
    # positions = something

    return gdf1 #todo fix what I'm returning here
