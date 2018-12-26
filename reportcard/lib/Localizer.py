import datetime, collections

import pandas as pd
import numpy as np

import geopandas
from scipy.spatial import cKDTree
from shapely.geometry import Point

from . import DataBases, BusAPI

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

    # CONVERSION OF DEGREES TO FEET
    #
    # current crude method, 1 degree = 69 miles = 364,320 feet
    df = pd.DataFrame.from_dict({'distance': (dist.astype(float)*364320),'bcol' : gdB.loc[idx, bcol].values })
    #
    # todo more accurate distance converstion
    # "@anthonymobile If CRS of geodfs are EPSG 4326 (lat/lon) then returned 'dist' will be in degrees. To meters or ft either first convert both gdf to appropriate CRS proj for your location using .to_crs() or convert from degrees (https://t.co/FODrAWskNH)
    #  additional reference https://gis.stackexchange.com/questions/279109/calculate-distance-between-a-coordinate-and-a-county-in-geopandas

    return df

# GET_NEAREST_STOP
#
# Finds the nearest stop, distance to it, from each item in a list of Bus objects.
# Returns as a list of BusPosition objects.
#


def get_buses_and_stops_sorted_by_direction(buses,route):


    # 2. ACQUIRE STOP LOCATIONS + CREATE GEODATAFRAMES for each service/direction
    routedata, coordinates_bundle = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data('nj', 'routes', route=route))

    # a. create stoplists by direction (ignoring services)

    stoplist = []
    for rt in routedata:
        for path in rt.paths:
            for p in path.points:
                if p.__class__.__name__ == 'Stop':
                    stoplist.append(
                        {'stop_id': p.identity, 'st': p.st, 'd': p.d, 'lat': p.lat, 'lon': p.lon})

    result = collections.defaultdict(list)
    for d in stoplist:
        result[d['d']].append(d)
    service_stoplist = list(result.values())

    #  b. sort the buses to matching stoplists
    buses_sorted_by_service = []
    for bus in buses:
        bus_list = []
        for service in service_stoplist:
            if bus.dd == service[0]['d']:
                bus_list.append(bus)
        buses_sorted_by_service.append(bus_list)

    return buses_sorted_by_service



def get_nearest_stop(buses,route):

    # 1. LOAD, FORMAT DATA + CREATE GEODATAFRAME FOR BUS POSITIONS

    if len(buses) == 0:
        bus_positions = []
        return bus_positions

    #convert Buses into dataframe
    df1 = pd.DataFrame.from_records([b.to_dict() for b in buses])

    df1['lat'] = pd.to_numeric(df1['lat'])
    df1['lon'] = pd.to_numeric(df1['lon'])

    # turn the bus positions df1 into a A GeoDataFrame
    # A GeoDataFrame needs a shapely object, so we create a new column Coordinates as a tuple of Longitude and Latitude :
    df1['coordinates'] = list(zip(df1.lon, df1.lat))
    # Then, we transform tuples to Point :
    df1['coordinates'] = df1['coordinates'].apply(Point)
    # Now, we can create the GeoDataFrame by setting geometry with the coordinates created previously.
    gdf1 = geopandas.GeoDataFrame(df1, geometry='coordinates')

    buses_and_stops = get_buses_and_stops_sorted_by_direction(buses,route)

    # c. create the geodataframes and run localization algorithm

    bus_positions = []
    for direction in buses_and_stops: # todo loop over each DIRECTION 'direction' below

        # turn it into a DF
        df2 = pd.DataFrame.from_records(direction)
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

        # insert inferred_stops back into gdf1
        gdf1=gdf1.join(inferred_stops)


        # d. convert geodataframe to a list of BusPosition objects

        for index, row in gdf1.iterrows():

            insertion=DataBases.BusPosition()

            insertion.lat = row.lat
            insertion.lon = row.lon
            insertion.cars = row.cars
            insertion.consist = row.consist
            insertion.d = row.d
            insertion.dip = row.dip
            insertion.dn = row.dn
            insertion.fs = row.fs
            insertion.id = row.id
            insertion.m = row.m
            insertion.op = row.op
            insertion.pd = row.pd
            insertion.pdRtpiFeedName = row.pdRtpiFeedName
            insertion.pid = row.pid
            insertion.rt = row.rt
            insertion.rtRtpiFeedName = row.rtRtpiFeedName
            insertion.rtdd = row.rtdd
            insertion.rtpiFeedName = row.rtpiFeedName
            insertion.run = row.run
            insertion.wid1 = row.wid1
            insertion.wid2 = row.wid2
            insertion.timestamp = row.timestamp
            insertion.trip_id = ('{id}_{run}_{dt}').format(id=row.id,run=row.run, dt=datetime.datetime.today().strftime('%Y-%m-%d'))
            insertion.stop_id =  row.stop_id,
            insertion.arrival_flag = False
            insertion.distance_to_stop = row.distance

        bus_positions.append(insertion)

    return bus_positions
