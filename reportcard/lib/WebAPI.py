import reportcard.lib.BusAPI as BusAPI
from reportcard.lib.DataBases import DBConfig, SQLAlchemyDBConnection, Trip, BusPosition, ScheduledStop
from reportcard.lib.TemplateContent import timestamp_fix
from sqlalchemy import func

import geojson
import pandas as pd
import datetime


# on-the-fly-GEOJSON-encoder
def positions2geojson(df):
    features = []
    df.apply(lambda X: features.append(
            geojson.Feature(geometry=geojson.Point((X["lon"],
                                                    X["lat"]    )),
                properties=dict(bid=X["bid"],
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

def build_filter():
        # build the query - based on https://goonan.io/building-queries-with-flask-sqlalchemy/
        # get the conditions from args into a list of tuples
        conditions = []
        for key, value in list(args.items()):
            conditions.append((key, value))
        if conditions != None:
            # turn it into a dict
            query = zip(conditions[0::2], conditions[1::2])
            # build query
            filters = []
            for conditions in query:
                if conditions[0] == 'id':
                    filters.append(BusPosition.id.in_(conditions[1].split(',')))
                else:
                    for term in conditions[1].split(','):
                        filters.append(BusPosition.__dict__[conditions[0]].ilike('%' + term + '%'))
        return filters


# POSITIONS ARGS-BASED
# /api/v1/positions?rt=87&period=now -- real-time from NJT API
# /api/v1/positions?rt=87&period={daily,yesterday,weekly,history} -- historical from routelog database
def get_positions_byargs(args):

    # for NOW, get current positions from NJT API
    if args['period'] == "now":
        positions = BusAPI.parse_xml_getBusesForRoute(BusAPI.get_xml_data('nj', 'buses_for_route', route=args['rt']))
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

        # positions_log = timestamp_fix(positions_log)
        positions_geojson = positions2geojson(positions_log)

    # for HISTORICAL, get positions from database
    else:
        with SQLAlchemyDBConnection(DBConfig.conn_str) as db

            query_filters=build_filter()

            if args['period'] == "daily":
                positions_log = BusPosition.query.filter(or_(*query_filters)) \
                    .filter(BusPosition.timestamp == func.current_date()) \
                    .order_by(BusPosition.timestamp.desc()) \

            elif args['period']  == "yesterday":
                # query = ('SELECT * FROM %s WHERE (%s AND (timestamp >= CURDATE() - INTERVAL 1 DAY AND timestamp < CURDATE())) ORDER BY timestamp DESC;' % (table_name, sql_insert))
                # todo adapt ORM-based query from daily above
                pass

            elif args['period']  == "weekly":
                # query = ('SELECT * FROM %s WHERE (%s AND (YEARWEEK(`timestamp`, 1) = YEARWEEK(CURDATE(), 1))) ORDER BY timestamp DESC;' % (table_name, sql_insert))
                # todo adapt ORM-based query from daily above
                pass

            elif args['period']  == "history":
                # query = ('SELECT * FROM %s WHERE %s ORDER BY timestamp DESC;' % (table_name, sql_insert))
                # todo adapt ORM-based query from daily above
                pass

            # elif kwargs['period']  like "2018-08-10":
                # todo adapt ORM-based query from daily above
                # query = ('SELECT * FROM %s WHERE (%s AND DATE(`timestamp`)=("2018-08-10") ORDER BY timestamp DESC;' % (table_name, sql_insert))

            # todo CONVERT THE SQLALCHEMY OBJECT TO A DF WITH THE RIGHT FORMAT
            # positions_log = pd.read_sql_query(query, conn)

            # cleanup
            positions_log = positions_log.drop(columns=['cars', 'consist', 'm','pdRtpiFeedName','rt','rtRtpiFeedName','rtdd','wid1','wid2'])
            positions_log = timestamp_fix(positions_log)
            positions_geojson = positions2geojson(positions_log)

    return positions_geojson







###################################################
#  old WebAPI.py
###################################################


#
# # ARRIVALS ARGS-BASED
# # /api/v1/arrivals?rt=87&period={daily,yesterday,weekly,history} -- historical from stop_approaches_log database
# def get_arrivals_byargs(args):
#
#     arrivals_log = StopReport(args['rt'],args['stop_id'],args['period']).arrivals_list_final_df
#     arrivals_log = arrivals_log.reset_index(drop=True)
#
#     arrivals_log['timestamp']=arrivals_log['timestamp'].astype(str)
#     arrivals_log = timestamp_fix(arrivals_log)
#
#     # arrivals_json = arrivals_log.to_json(orient='records')
#
#     return arrivals_log
#
#
#
# # HOURLY FREQUENCY HISTOGRAM - BY ROUTE, STOP, PERIOD
# # /api/v1/frequency?rt=87&stop_id=87&period={daily,yesterday,weekly,history}
# def get_frequency_byargs(args):
#
#     frequency_histogram = StopReport(args['rt'],args['stop_id'],args['period']).get_hourly_frequency(args['rt'],args['stop_id'],args['period'])
#
#     return frequency_histogram
#
# def render_citywide_map_geojson(reportcard_routes):
#
#
#     waypoints = []
#     stops = []
#
#     for i in reportcard_routes:
#         routedata, waypoints_raw, stops_raw, a, b = BusAPI.parse_xml_getRoutePoints(
#             BusAPI.get_xml_data('nj', 'routes', route=i['route']))
#
#
#         waypoints_feature = geojson.Feature(geometry=geojson.LineString(waypoints_raw))
#         stops_feature = geojson.Feature(geometry=geojson.MultiPoint(stops_raw))
#
#         waypoints.append(waypoints_feature)
#         stops.append(stops_feature)
#
#     citywide_waypoints = geojson.FeatureCollection(waypoints)
#     citywide_stops = geojson.FeatureCollection(stops)
#
#     return citywide_waypoints, citywide_stops