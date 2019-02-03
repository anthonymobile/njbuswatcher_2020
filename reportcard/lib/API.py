import lib.BusAPI as BusAPI
from lib.DataBases import DBConfig, SQLAlchemyDBConnection, Trip, BusPosition, ScheduledStop
from lib.wwwAPI import timestamp_fix
from sqlalchemy import func
from sqlalchemy.sql.expression import and_

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

# POSITIONS ARGS-BASED
# /api/v1/positions?rt=87&period=now -- real-time from NJT API
# /api/v1/positions?rt=87&period={daily,yesterday,history} -- historical from positions_log table
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
        with SQLAlchemyDBConnection(DBConfig.conn_str) as db:
            today = datetime.date.today()
            yesterday = datetime.date.today() - datetime.timedelta(1)
            request_filters = {i: args[i] for i in args if i != 'period'}
            print (request_filters)

            if args['period'] == "today":

                # query into a pandas df
                # from https://stackoverflow.com/questions/29525808/sqlalchemy-orm-conversion-to-pandas-dataframe
                if args['period'] == "today":
                    positions_log = pd.read_sql(db.session.query(BusPosition).filter_by(**request_filters)
                        .filter(BusPosition.timestamp == today)
                        .order_by(BusPosition.timestamp.desc()).statement
                        ,db.session.bind)

            elif args['period']  == "yesterday":
                pass
                # positions_log = pd.read_sql(db.session.query(BusPosition).filter(and_(*query_filters))
                #     .filter(BusPosition.timestamp >= yesterday)
                #     .filter(BusPosition.timestamp != today)
                #     .order_by(BusPosition.timestamp.desc())
                #     , db.session.bind)

            elif args['period']  == "history":
                pass
                # positions_log = pd.read_sql(db.session.query(BusPosition).filter(and_(*query_filters))
                #     .order_by(BusPosition.timestamp.desc())
                #     , db.session.bind)

            elif args['period'] is True:
                pass
                # try:
                #     int(args['period']) # check if it digits (e.g. period=20180810)
                #     query_date = datetime.datetime.strptime(args['period'], '%Y%m%d') # make a datetime object
                #     positions_log = pd.read_sql(db.session.query(BusPosition).filter(and_(*query_filters))
                #         .filter(BusPosition.timestamp == query_date)
                #         .order_by(BusPosition.timestamp.desc())
                #         , db.session.bind)
                # except ValueError:
                #     pass


            # cleanup
            positions_log = positions_log.drop(columns=['cars', 'consist', 'm','pdrtpifeedname','rt','rtrtpifeedname','rtdd','wid1','wid2'])
            positions_log = timestamp_fix(positions_log)
            positions_geojson = positions2geojson(positions_log)

    return positions_geojson


