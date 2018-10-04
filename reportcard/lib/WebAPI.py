# handles the API for the bustracker app itself

import BusRouteLogsDB
from ReportCard import timestamp_fix
import geojson
import pandas as pd

try:
    db_state = os.environ['REPORTCARD_PRODUCTION']
    db_server = '192.168.1.181'
except:
    db_server = '127.0.0.1'


def data2geojson(df):
    features = []
    df.apply(lambda X: features.append(
            geojson.Feature(geometry=geojson.Point((X["lon"],
                                                    X["lat"]    )),
                properties=dict(v=X["bid"],
                                timestamp=X["timestamp"],
                                description=unicode(X["pd"].decode('utf8'))))
                                    )
            , axis=1)


    # return geojson.dumps(geojson.FeatureCollection(features), indent=4, sort_keys=True, default=str)
    return geojson.FeatureCollection(features)



def get_positions_byurl(route, period, **kwargs):

    # database initialization
    db = BusRouteLogsDB.MySQL('buses', 'buswatcher', 'njtransit', db_server, route)
    conn = db.conn

    table_name = 'routelog_' + route

    if period == "daily":
        query = ('SELECT * FROM %s WHERE (rt=%s AND DATE(`timestamp`)=CURDATE() ) ORDER BY timestamp DESC;' % (
            table_name, route))
    elif period == "yesterday":
        query = (
                'SELECT * FROM %s WHERE (rt=%s AND (timestamp >= CURDATE() - INTERVAL 1 DAY AND timestamp < CURDATE())) ORDER BY timestamp DESC;' % (
            table_name, route))
    elif period == "weekly":
        query = (
                'SELECT * FROM %s WHERE (rt=%s AND (YEARWEEK(`timestamp`, 1) = YEARWEEK(CURDATE(), 1))) ORDER BY timestamp DESC;' % (
            table_name, route))
    elif period == "history":
        query = ('SELECT * FROM %s WHERE rt=%s ORDER BY timestamp DESC;' % (table_name, route))
    # elif period like "2018-08-10":
        # query = ('SELECT * FROM %s WHERE (rt=%s AND DATE(`timestamp`)=("2018-08-10") ORDER BY timestamp DESC;' % (table_name, route))
        raise RuntimeError('Bad request sucker!')

    # if v is not None:
    #     query = # regexp replace the first AND with 'AND v=%s v') or something like that

    # get data and basic cleanup
    positions_log = pd.read_sql_query(query, conn)
    # df_temp = df_temp.drop(columns=['cars', 'consist', 'fd', 'm', 'name', 'rn', 'scheduled'])
    positions_log = timestamp_fix(positions_log)

    positions_geojson = data2geojson(positions_log)

    return positions_geojson


def get_positions_byargs(args):

    # database initialization
    db = BusRouteLogsDB.MySQL('buses', 'buswatcher', 'njtransit', db_server, args['rt'])
    conn = db.conn

    table_name = 'routelog_' + args['rt']


    sql_insert=str()
    for key, value in args.items():
        if key == 'period':
            pass
        else:
            _sql_snippet = (" AND {}={}").format(key,value)
            sql_insert+=_sql_snippet
    # todo regexp find and delete first instance of " AND "
    sql_insert=("("+sql_insert+")")


    try:
        if args['period'] == "daily":
            query = ('SELECT * FROM %s WHERE (%s AND DATE(`timestamp`)=CURDATE() ) ORDER BY timestamp DESC;' % (
                table_name, sql_insert))
        elif args['period']  == "yesterday":
            query = (
                    'SELECT * FROM %s WHERE (%s AND (timestamp >= CURDATE() - INTERVAL 1 DAY AND timestamp < CURDATE())) ORDER BY timestamp DESC;' % (
                table_name, sql_insert))
        elif args['period']  == "weekly":
            query = (
                    'SELECT * FROM %s WHERE (%s AND (YEARWEEK(`timestamp`, 1) = YEARWEEK(CURDATE(), 1))) ORDER BY timestamp DESC;' % (
                table_name, sql_insert))
        elif args['period']  == "history":
            query = ('SELECT * FROM %s WHERE %s ORDER BY timestamp DESC;' % (table_name, sql_insert))
        # elif kwargs['period']  like "2018-08-10":
            # query = ('SELECT * FROM %s WHERE (%s AND DATE(`timestamp`)=("2018-08-10") ORDER BY timestamp DESC;' % (table_name, sql_insert))
            raise RuntimeError('Bad request sucker!')

    except:
        # no period defined, fetch entire history

        query = ('SELECT * FROM %s WHERE %s ORDER BY timestamp DESC;' % (table_name, sql_insert))

    # remove the leading AND in query
    query = query.replace(' AND ', '',1)

    # get data and basic cleanup
    positions_log = pd.read_sql_query(query, conn)
    # df_temp = df_temp.drop(columns=['cars', 'consist', 'fd', 'm', 'name', 'rn', 'scheduled'])
    positions_log = timestamp_fix(positions_log)

    positions_geojson = data2geojson(positions_log)

    return positions_geojson


def get_arrivals(route,stop,period, args):
    # if v not None:
    #     then get for single bus
    # if period = blah:
    #     query =
    # elif
    # elif
    # elif
    #
    # positions_log = db.MySQL.fetch_records(elf, db_name, db_user, db_password, db_host, route)
    #
    # geojsonify something
    return