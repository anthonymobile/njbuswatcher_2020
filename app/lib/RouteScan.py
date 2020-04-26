import datetime, time
import itertools
import collections

import pandas as pd
import numpy as np
import geopandas

from pymysql import IntegrityError
from scipy.spatial import cKDTree
from shapely.geometry import Point

from .DataBases import SQLAlchemyDBConnection, Trip, BusPosition, ScheduledStop
from . import NJTransitAPI
from .CommonTools import timeit
# from .TransitSystem import load_system_map

class RouteScan:

    def __init__(self, system_map):

        self.source = 'nj'

        # create database connection
        self.db = SQLAlchemyDBConnection()

        # initialize instance variables
        self.buses = []
        self.trip_list = []

        # generate scan data and results

        self.fetch_positions()
        self.parse_positions(system_map)
        self.localize_positions(system_map)
        self.assign_positions()
        self.interpolate_missed_stops()

    def fetch_positions(self):

        try:
            self.buses = NJTransitAPI.parse_xml_getBusesForRouteAll(NJTransitAPI.get_xml_data('nj', 'all_buses'))
            route_count = len(list(set([v.rt for v in self.buses])))
            print('\rfetched ' + str(len(self.buses)) + ' buses on ' + str(route_count) + ' routes...')
            # self.clean_buses()
        except:
            pass

        return

    def parse_positions(self, system_map):

        with self.db as db:

            # PARSE trips, create missing trip records first, to honor foreign key constraints
            for bus in self.buses:
                bus.trip_id = ('{id}_{run}_{dt}').format(id=bus.id, run=bus.run, dt=datetime.datetime.today().strftime('%Y%m%d'))
                self.trip_list.append(bus.trip_id)
                result = db.session.query(Trip).filter(Trip.trip_id == bus.trip_id).first()

                try:
                    if result is None:
                        trip_id = Trip('nj', system_map, bus.rt, bus.id, bus.run, bus.pd, bus.pid)
                        db.session.add(trip_id)
                    else:
                        continue
                except:
                    print("couldn't find route in route_descriptions.json, please add it. route " + str(
                        bus.rt))

                db.__relax__()  # disable foreign key checks before...
                try:
                    db.session.commit()  # we save the position_log.
                except IntegrityError:
                    print('another integrity error writing these arrivals to the db')
                    db.session.rollback()
            # print ('parsed {a} trips'.format(a=len(self.trip_list)))
            return

    def localize_positions(self, system_map):

        with self.db as db:

            try:

                statewide_route_list = sorted(
                    list(set([bus.rt for bus in self.buses])))  # find all the routes unique
                for r in statewide_route_list:  # loop over each route

                    try:
                        buses_for_this_route = [b for b in self.buses if b.rt == r]
                        bus_positions = get_nearest_stop(system_map, buses_for_this_route, r)

                        for group in bus_positions:
                            for bus in group:
                                db.session.add(bus)
                        db.__relax__()  # disable foreign key checks before commit
                        db.session.commit()
                    except:
                        pass



            except (IntegrityError) as e:
                error_count = + 1
                print(e + 'mysql integrity error #' + error_count)

        return

    def assign_positions(self):

        with self.db as db:

            # ASSIGN TO NEAREST STOP
            for trip_id in self.trip_list:

                # load the trip card for reference
                scheduled_stops = db.session.query(Trip, ScheduledStop) \
                    .join(ScheduledStop) \
                    .filter(Trip.trip_id == trip_id) \
                    .all()

                # select all the BusPositions on ScheduledStops where there is no arrival flag yet
                arrival_candidates = db.session.query(BusPosition) \
                    .join(ScheduledStop) \
                    .filter(BusPosition.trip_id == trip_id) \
                    .filter(ScheduledStop.arrival_timestamp == None) \
                    .order_by(BusPosition.timestamp.asc()) \
                    .all()

                # split them into groups by stop
                position_groups = [list(g) for key, g in itertools.groupby(arrival_candidates, lambda x: x.stop_id)]

                # iterate over all but last one (which is stop bus is currently observed at)
                for x in range(len(position_groups) - 1):

                    # slice the positions for the xth stop
                    position_list = position_groups[x]

                    # GRAB THE STOP RECORD FROM DB FOR UPDATING ARRIVAL INFO
                    stop_to_update = db.session.query(ScheduledStop, BusPosition) \
                        .join(BusPosition) \
                        .filter(ScheduledStop.trip_id == position_list[0].trip_id) \
                        .filter(ScheduledStop.stop_id == position_list[0].stop_id) \
                        .all()

                    ##############################################
                    #   ONE POSITION
                    #   if we only have one observation and since
                    #   this isn't the current stop, then we've
                    #   already passed it and can just assign it
                    #   as the arrival
                    ##############################################

                    if len(position_list) == 1:
                        arrival_time = position_list[0].timestamp
                        position_list[0].arrival_flag = True
                        case_identifier = '1a'
                        approach_array = np.array([0, position_list[0].distance_to_stop])

                    ##############################################
                    #   TWO POSITIONS
                    #   calculate the slope between the two points
                    #   and assign to CASE A,B, or C
                    #   arrival is either the 1st observed position
                    #   or the 2nd
                    ##############################################

                    elif len(position_list) == 2:

                        # create and display approach array
                        points = []
                        for y in range(len(position_list)):
                            points.append((y, position_list[y].distance_to_stop))
                        approach_array = np.array(points)

                        # calculate classification metrics
                        slope = np.diff(approach_array, axis=0)[:, 1]
                        acceleration = np.diff(slope, axis=0)
                        slope_avg = np.mean(slope, axis=0)

                        # CASE A sitting at the stop, then gone without a trace
                        # determined by [d is <100, doesn't change e.g. slope = 0 ]
                        # (0, 50)  <-----
                        # (1, 50)
                        if slope_avg == 0:
                            arrival_time = position_list[0].timestamp
                            position_list[0].arrival_flag = True
                            case_identifier = '2a'

                        # CASE B approaches, then vanishes
                        # determined by [d is decreasing, slope is always negative]
                        # (0, 400)
                        # (1, 300) <-----
                        elif slope_avg < 0:
                            arrival_time = position_list[-1].timestamp
                            position_list[-1].arrival_flag = True
                            case_identifier = '2b'

                        # CASE C appears, then departs
                        # determined by [d is increasing, slope is always positive]
                        # (0, 50)  <-----
                        # (1, 100)
                        elif slope_avg > 0:
                            arrival_time = position_list[0].timestamp
                            position_list[0].arrival_flag = True
                            case_identifier = '2c'

                    ##############################################
                    #   THREE OR MORE POSITIONS
                    ##############################################

                    elif len(position_list) > 2:

                        # create and display approach array
                        # print(('\tapproaching {b}').format(a=trip_id, b=position_list[0].stop_id))
                        points = []
                        for y in range(len(position_list)):
                            points.append((y, position_list[y].distance_to_stop))
                        approach_array = np.array(points)
                        # for point in approach_array:
                        # print(('\t\t {a:.0f} distance_to_stop {b}').format(a=point[0], b=point[1]))

                        # calculate classification metrics
                        slope = np.diff(approach_array, axis=0)[:, 1]
                        acceleration = np.diff(slope, axis=0)
                        slope_avg = np.mean(slope, axis=0)

                        try:
                            # CASE A
                            if slope_avg == 0:
                                arrival_time = position_list[0].timestamp
                                position_list[0].arrival_flag = True
                                case_identifier = '3a'
                                # plot_approach(trip_id, np.array([0, position_list[0].distance_to_stop]), case_identifier)

                            # CASE B
                            elif slope_avg < 0:
                                arrival_time = position_list[-1].timestamp
                                position_list[-1].arrival_flag = True
                                case_identifier = '3b'
                                # plot_approach(trip_id, np.array([0, position_list[-1].distance_to_stop]), case_identifier)

                            # CASE C
                            elif slope_avg > 0:
                                arrival_time = position_list[0].timestamp
                                position_list[0].arrival_flag = True
                                case_identifier = '3c'
                                # plot_approach(trip_id, np.array([0, position_list[0].distance_to_stop]), case_identifier)

                            # to do add 2 `Boomerang buses (Case D)`

                        except:
                            pass

                    # catch errors for unassigned 3+-position approaches
                    # to do 2 debug approach assignment: 3+ position seems to still be having problems...
                    try:
                        stop_to_update[0][0].arrival_timestamp = arrival_time
                    except:
                        pass

            db.session.commit()

            return

    @timeit
    def interpolate_missed_stops(self):


        print ('starting interpolations for {a} trips...'.format(a=len(self.trip_list)))

        # grab a trip
        for trip_id in self.trip_list:

            with self.db as db:
                trip_card = db.session.query(ScheduledStop) \
                    .join(Trip) \
                    .filter(Trip.trip_id == trip_id) \
                    .order_by(ScheduledStop.pkey.asc()) \
                    .all()

                # count up the number of arrivals
                num_arrivals=0
                for scheduled_stop in trip_card:
                    if scheduled_stop.arrival_timestamp is not None:
                        num_arrivals += 1

                # deal with common situations to skip the CPU intensive stuff
                if num_arrivals == 0:
                    # print('\t\tdoesnt have any arrivals logged yet')
                    continue # back to loop start
                elif num_arrivals == 1:
                    # print('\t\thas 1 arrival, so no intervals yet to interpolate')
                    continue # back to loop start
                elif num_arrivals == len (trip_card):
                    # print('\t\tdoesnt have any missed stops')
                    continue # back to loop start

                # MAIN SCAN LOOP

                # initialize
                in_interval=False
                all_this_trips_intervals = {}
                # dict_insert ={}

                # go through the scheduled_stops
                for scheduled_stop in trip_card:
                    # find an arrival
                    if scheduled_stop.arrival_timestamp:
                        if in_interval == False:
                            # print('\tstarting interval at stop {a}\t{b}'.format(a=scheduled_stop.stop_id,b=scheduled_stop.arrival_timestamp))
                            interval_stops = []
                            interval_stops.append(scheduled_stop) # these should be pointers to the object, not copies
                            in_interval = True
                            continue
                        elif in_interval == True:
                            # print('\tending interval at stop {a}\t{b}'.format(a=scheduled_stop.stop_id,b=scheduled_stop.arrival_timestamp))
                            interval_stops.append(scheduled_stop)
                            # dict_insert[interval_stops[0].stop_id]=interval_stops
                            all_this_trips_intervals[interval_stops[0].stop_id] = interval_stops # create a dict entry with k of first stop_id, v of list of stop instances
                            # reinit
                            interval_stops = []
                            in_interval = False
                            # dict_insert={}
                            continue
                    elif scheduled_stop.arrival_timestamp is None:
                        if in_interval == False:
                            continue
                        elif in_interval == True:
                            # print('\t\tno timestamp for stop {a}'.format(a=scheduled_stop.stop_id))
                            interval_stops.append(scheduled_stop)
                            continue
                    else:
                        print ('****************** This one fell through the gap {a}'.format(a=scheduled_stop))
                        continue

                # INTERPOLATION LOOP

                # analyze all_the_intervals
                for stop_id, interval_sequence in all_this_trips_intervals.items():

                    print('trip {a}'.format(a=trip_id))

                    start_time = interval_sequence[0].arrival_timestamp
                    end_time = interval_sequence[-1].arrival_timestamp
                    interval_length = (len(interval_sequence) - 1)
                    average_time_between_stops = (end_time - start_time) / interval_length
                    print('\tinterval starts at {a} ends at {b} has {c} gaps averaging {d} seconds'.format(a=interval_sequence[0].stop_id, b= interval_sequence[-1].stop_id, c=interval_length, d=average_time_between_stops))

                    # update the ScheduledStop objects
                    n = 1
                    for x in range(1,(len(interval_sequence)-1)):
                        adder = average_time_between_stops * n
                        interval_sequence[x].arrival_timestamp = start_time + adder
                        interval_sequence[x].interpolated_arrival_flag = True
                        n += 1
                        print('\t\tarrival_timestamp added to ScheduledStop instance for stop {a}\t{b}\tincrement {c}'.format(a=interval_sequence[x].stop_id, b=interval_sequence[x].arrival_timestamp, c=adder))

                # when we are done with this trip, write to the db
                db.session.commit()

        print ('****************** interpolation done ******************')


    def get_current_trips(self):
        # get a list of trips current running the route
        v_on_route = NJTransitAPI.parse_xml_getBusesForRoute(
            NJTransitAPI.get_xml_data(self.source, 'buses_for_route', route=self.route))
        todays_date = datetime.datetime.today().strftime('%Y%m%d')
        trip_list = list()
        trip_list_trip_id_only = list()

        for v in v_on_route:
            trip_id = ('{a}_{b}_{c}').format(a=v.id, b=v.run, c=todays_date)
            trip_list.append((trip_id, v.pd, v.bid, v.run))
            trip_list_trip_id_only.append(trip_id)

        return trip_list, trip_list_trip_id_only


def turn_row_into_BusPosition(row):

    position = BusPosition()
    position.lat = row.lat
    position.lon = row.lon
    position.cars = row.cars
    position.consist = row.consist
    position.d = row.d
    position.dn = row.dn
    position.fs = row.fs
    position.id = row.id
    position.m = row.m
    position.op = row.op
    position.pd = row.pd
    position.pdrtpifeedname = row.pdRtpiFeedName
    position.pid = row.pid
    position.rt = row.rt
    position.rtrtpifeedname = row.rtRtpiFeedName
    position.rtdd = row.rtdd
    position.rtpifeedname = row.rtpiFeedName
    position.run = row.run
    position.wid1 = row.wid1
    position.wid2 = row.wid2

    position.trip_id = ('{id}_{run}_{dt}').format(id=row.id, run=row.run,
                                                  dt=datetime.datetime.today().strftime('%Y%m%d'))
    position.arrival_flag = False
    position.distance_to_stop = row.distance
    position.stop_id = row.stop_id
    position.timestamp = datetime.datetime.now()

    return position

def ckdnearest(gdA, gdB, bcol):

    ###########################################################################
    # CKDNEAREST
    # https://gis.stackexchange.com/questions/222315/geopandas-find-nearest-point-in-other-dataframe
    # Here is a helper function that will return the distance and 'Name'
    # of the nearest neighbor in gpd2 from each point in gpd1.
    # It assumes both gdfs have a geometry column (of points).
    ###########################################################################

    nA = np.array(list(zip(gdA.geometry.x, gdA.geometry.y)))
    nB = np.array(list(zip(gdB.geometry.x, gdB.geometry.y)))
    btree = cKDTree(nB)
    dist, idx = btree.query(nA, k=1)

    # CONVERSION OF DEGREES TO FEET

    # current crude method, 1 degree = 69 miles = 364,320 feet
    df = pd.DataFrame.from_dict({'distance': (dist.astype(float) * 364320), bcol: gdB.loc[idx, bcol].values})


    # # new method based on https://gis.stackexchange.com/questions/279109/calculate-distance-between-a-coordinate-and-a-county-in-geopandas
    # from math import radians, cos, sin, asin, sqrt
    #
    # def haversine(lon1, lat1, lon2, lat2):
    #     # Calculate the great circle distance between two points on the earth (specified in decimal degrees)
    #     lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    #     dlon = lon2 - lon1
    #     dlat = lat2 - lat1
    #     a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    #     c = 2 * asin(sqrt(a))
    #     r = 3956  # Radius of earth in miles. Use 6371 for kilometers
    #     return c * r
    #
    # df = pd.DataFrame.from_dict({'distance': (haversine(gdA.geometry.x, gdA.geometry.y, gdB.geometry.x, gdB.geometry.y)),bcol : gdB.loc[idx, bcol].values })
    #
    # # EXAMPLE OF ITERATING OVER A GDF
    # # for index, row in gdf.iterrows():
    # #     for pt in list(row['geometry'].exterior.coords):
    #

    return df

def get_nearest_stop(system_map, buses, route):
    ###########################################################################
    # GET_NEAREST_STOP
    #
    # Finds the nearest stop, distance to it, from each item in a list of Bus objects.
    # Returns as a list of BusPosition objects.
    #
    ###########################################################################

    # routedata, coordinates_bundle = system_map.get_single_route_paths_and_coordinatebundle(route)

    # sort bus data into directions
    buses_as_dicts = [b.to_dict() for b in buses]
    result2 = collections.defaultdict(list)
    for b in buses_as_dicts:
        result2[b['dd']].append(b)
    buses_by_direction = list(result2.values())
    if len(buses) == 0:
        bus_positions = []
        return bus_positions

    try:
        stoplist = system_map.get_single_route_stoplist_for_localizer(route)
    except:

        print("couldn't find route in route_descriptions.json, please add it. route " + str(route))
        return

    result = collections.defaultdict(list)
    for d in stoplist:
        result[d['d']].append(d)
    stops_by_direction = list(result.values())

    # loop over the directions in buses_by_direction
    bus_positions = []
    for bus_direction in buses_by_direction:
        # create bus geodataframe
        df1 = pd.DataFrame.from_records(bus_direction)
        df1['lat'] = pd.to_numeric(df1['lat'])
        df1['lon'] = pd.to_numeric(df1['lon'])
        df1['coordinates'] = list(zip(df1.lon, df1.lat))
        df1['coordinates'] = df1['coordinates'].apply(Point)
        gdf1 = geopandas.GeoDataFrame(df1, geometry='coordinates')

        # create stop geodataframe

        for stop_direction in stops_by_direction:
            if bus_direction[0]['dd'] == stop_direction[0]['d']:

                df2 = pd.DataFrame.from_records(stop_direction)
                df2['lat'] = pd.to_numeric(df2['lat'])
                df2['lon'] = pd.to_numeric(df2['lon'])

                df2['coordinates'] = list(zip(df2.lon, df2.lat))
                df2['coordinates'] = df2['coordinates'].apply(Point)
                gdf2 = geopandas.GeoDataFrame(df2, geometry='coordinates')

                # call localizer
                inferred_stops = ckdnearest(gdf1, gdf2, 'stop_id')

                gdf1['stop_id'] = inferred_stops['stop_id']
                gdf1['distance'] = inferred_stops['distance']

                bus_list = gdf1.apply(lambda row: turn_row_into_BusPosition(row), axis=1)

                bus_positions.append(bus_list)

            else:
                pass

    return bus_positions
