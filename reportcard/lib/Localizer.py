###########################################################################
# Localizer
###########################################################################

import datetime, collections

import pandas as pd
import numpy as np

import geopandas
from scipy.spatial import cKDTree
from shapely.geometry import Point

from . import DataBases, BusAPI


###########################################################################
# CKDNEAREST
# https://gis.stackexchange.com/questions/222315/geopandas-find-nearest-point-in-other-dataframe
# Here is a helper function that will return the distance and 'Name'
# of the nearest neighbor in gpd2 from each point in gpd1.
# It assumes both gdfs have a geometry column (of points).
###########################################################################

def ckdnearest(gdA, gdB, bcol):
    nA = np.array(list(zip(gdA.geometry.x, gdA.geometry.y)) )
    nB = np.array(list(zip(gdB.geometry.x, gdB.geometry.y)) )
    btree = cKDTree(nB)
    dist, idx = btree.query(nA,k=1)

    # CONVERSION OF DEGREES TO FEET
    #
    # current crude method, 1 degree = 69 miles = 364,320 feet
    df = pd.DataFrame.from_dict({'distance': (dist.astype(float)*364320),bcol : gdB.loc[idx, bcol].values })
    #
    # todo more accurate distance converstion
    # "@anthonymobile If CRS of geodfs are EPSG 4326 (lat/lon) then returned 'dist' will be in degrees. To meters or ft either first convert both gdf to appropriate CRS proj for your location using .to_crs() or convert from degrees (https://t.co/FODrAWskNH)
    #  additional reference https://gis.stackexchange.com/questions/279109/calculate-distance-between-a-coordinate-and-a-county-in-geopandas

    return df




###########################################################################
# GET_NEAREST_STOP
#
# Finds the nearest stop, distance to it, from each item in a list of Bus objects.
# Returns as a list of BusPosition objects.
#
###########################################################################

def get_nearest_stop(buses,route):

    # sort bus data into directions

    buses_as_dicts = [b.to_dict() for b in buses]
    result2 = collections.defaultdict(list)

    for b in buses_as_dicts:
        result2[b['dd']].append(b)
    buses_by_direction = list(result2.values())

    if len(buses) == 0:
        bus_positions = []
        return bus_positions

    # acquire and sort stop data in directions (ignoring services)

    routedata, coordinates_bundle = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data('nj', 'routes', route=route))
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
    stops_by_direction = list(result.values())     # todo remove duplicate stop_id (not simple, maybe not faster, only do if causing errors)

    # loop over the directions in buses_by_direction

    bus_positions = []

    for bus_direction in buses_by_direction: # todo its running one of these loops 2x

        # create bus geodataframe
        #df1 = pd.DataFrame.from_records([b.to_dict() for b in buses])
        df1 = pd.DataFrame.from_records(bus_direction)
        df1['lat'] = pd.to_numeric(df1['lat'])
        df1['lon'] = pd.to_numeric(df1['lon'])
        df1['coordinates'] = list(zip(df1.lon, df1.lat))
        df1['coordinates'] = df1['coordinates'].apply(Point)
        gdf1 = geopandas.GeoDataFrame(df1, geometry='coordinates')

        # create stop geodataframe

        # turn stops_by_direction into a dict with:
        # pandas.DataFrame.from_records([s.to_dict() for s in signals])

        for stop_direction in stops_by_direction: # todo its running one of these loops 2x
            if bus_direction[0]['dd'] == stops_by_direction[0][0]['d']:

                df2=pd.DataFrame.from_records(stop_direction)
                df2['lat'] = pd.to_numeric(df2['lat'])
                df2['lon'] = pd.to_numeric(df2['lon'])

                df2['coordinates'] = list(zip(df2.lon, df2.lat))
                df2['coordinates'] = df2['coordinates'].apply(Point)
                gdf2 = geopandas.GeoDataFrame(df2, geometry='coordinates')

                # call localizer
                inferred_stops = ckdnearest(gdf1, gdf2, 'stop_id')

                gdf1['stop_id'] = inferred_stops['stop_id']
                gdf1['distance'] = inferred_stops['distance']


                # serialize as a list of BusPosition objects

                bus_list = []

                for index, row in gdf1.iterrows():
                    position = DataBases.BusPosition()

                    position.lat = row.lat
                    position.lon = row.lon
                    position.cars = row.cars
                    position.consist = row.consist
                    position.d = row.d
                    position.dip = row.dip
                    position.dn = row.dn
                    position.fs = row.fs
                    position.id = row.id
                    position.m = row.m
                    position.op = row.op
                    position.pd = row.pd
                    position.pdRtpiFeedName = row.pdRtpiFeedName
                    position.pid = row.pid
                    position.rt = row.rt
                    position.rtRtpiFeedName = row.rtRtpiFeedName
                    position.rtdd = row.rtdd
                    position.rtpiFeedName = row.rtpiFeedName
                    position.run = row.run
                    position.wid1 = row.wid1
                    position.wid2 = row.wid2

                    position.trip_id = ('{id}_{run}_{dt}').format(id=row.id, run=row.run, dt=datetime.datetime.today().strftime('%Y%m%d'))
                    position.arrival_flag = False
                    position.distance_to_stop = row.distance
                    position.stop_id = row.stop_id  # todo where to get this from?
                    position.timestamp = datetime.datetime.now()  # todo add timestamp now or later?

                    bus_list.append(position)

                bus_positions.append(bus_list)

            else:
                pass



    return bus_positions
