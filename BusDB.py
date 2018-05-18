import os
import sqlite3
from mysql.connector import connection
import mongoengine as mongo
import datetime

_columns = ['lat','lon','ar','bid','c','cars','consist','d','dd','dn','fs','id','m','op','pd','pdRtpiFeedName','pid','rt','rtRtpiFeedName','rtdd','rtpiFeedName','run','wid1','wid2']
_stop_columns = ['cars','consist','fd','m','name','pt','rd','rn','scheduled','stop_id','stop_name','v']


def _bus_to_sql(format_string, bus, timestamp):
    for var in _columns:
        if not hasattr(bus, var):
            if var == 'lat' or var == 'lon':
                setattr(bus, var, 0.0)
            else:
                setattr(bus, var, '')

    return format_string % (
    float(bus.lat), float(bus.lon), bus.ar, bus.bid, bus.c, bus.cars, bus.consist, bus.d, bus.dd, bus.dn, bus.fs,
    bus.id, bus.m, bus.op, bus.pd, bus.pdRtpiFeedName, bus.pid, bus.rt, bus.rtRtpiFeedName, bus.rtdd, bus.rtpiFeedName,
    bus.run, bus.wid1, bus.wid2, str(timestamp))


def _bus_to_instance(bus, timestampnow):     # i turn a bus record into an instance of the Position class
    bus_position = Position(
                        lat=bus.lat,
                        lon=bus.lon,
                        bid=bus.bid,
                        c=bus.c,
                        cars=bus.cars,
                        consist=bus.consist,
                        d=bus.d,
                        dd=bus.dd,
                        dn=bus.dn,
                        fs=bus.fs,
                        id_bus=bus.id,
                        m=bus.m,
                        op=bus.op,
                        pd=bus.pd,
                        pdRtpiFeedName=bus.pdRtpiFeedName,
                        pid=bus.pid,
                        rt=bus.rt,
                        rtRtpiFeedName=bus.rtRtpiFeedName,
                        rtdd=bus.rtdd,
                        rtpiFeedName=bus.rtpiFeedName,
                        run=bus.run,
                        wid1=bus.wid1,
                        wid2=bus.wid2,
                        )
    return bus_position


class DB:
    def __init__(self, insert_string):
        self.conn = None
        self.insert_string = insert_string

    def __del__(self):
        if self.conn is not None:
            self.conn.close()

    def _execute(self, command):
        self._batch_execute([command])

    def _batch_execute(self, commands):
        cursor = self.conn.cursor()
        for command in commands:
            cursor.execute(command)
        self.conn.commit()

    def insert_positions(self, records, timestamp):
        import ipdb
        # ipdb.set_trace()
        self._batch_execute([_bus_to_sql(self.insert_string, r, timestamp) for r in records])


class SQLite(DB):
    _create_db_string = '''CREATE TABLE buses (pkey integer primary key autoincrement, lat real, lon real, ar text, bid text, c text, cars text, consist text, d text, dd text, dn text, fs text, id text, m text, op text, pd text, pdRtpiFeedName text, pid text, rt text, rtRtpiFeedName text, rtdd text, rtpiFeedName text, run text, wid1 text, wid2 text, timestamp text)'''

    _insert_string = 'INSERT INTO buses VALUES(NULL, %f, %f, "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s")'

    def __init__(self, fname):
        DB.__init__(self, SQLite._insert_string)
        self.conn = None
        self.fname = fname

        if not os.path.exists(self.fname):
            if not os.path.exists(os.path.dirname(self.fname)):
                os.makedirs(os.path.dirname(self.fname))
            self.conn = sqlite3.connect(self.fname)
            self._execute(SQLite._create_db_string)
        else:
            self.conn = sqlite3.connect(self.fname)

class SQLite_Stops(DB):
    _create_db_string = '''CREATE TABLE stops (pkey integer primary key autoincrement, cars text, consist text, fd text, m text, name text, pt text, rd text, rn text, scheduled text, stop_id text, stop_name text, v text, timestamp text)'''

    _insert_string = 'INSERT INTO stop_predictions VALUES(NULL, "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s")'

    def __init__(self, fname):
        DB.__init__(self, SQLite_Stops._insert_string)
        self.conn = None
        self.fname = fname

        if not os.path.exists(self.fname):
            if not os.path.exists(os.path.dirname(self.fname)):
                os.makedirs(os.path.dirname(self.fname))
            self.conn = sqlite3.connect(self.fname)
            self._execute(SQLite_Stops._create_db_string)
        else:
            self.conn = sqlite3.connect(self.fname)


    def _stops_to_sql(format_string, stopprediction, timestamp):
        for var in _stop_columns:
            if not hasattr(stopprediction, var):
                print var
                print stopprediction
                setattr(stopprediction, var, '')

        return format_string % (stopprediction.cars, stopprediction.consist, stopprediction.fd, stopprediction.m, stopprediction.name, stopprediction.pt, stopprediction.rd, stopprediction.rn, stopprediction.scheduled, stopprediction.stop_id, stopprediction.stop_name, stopprediction.v, str(timestamp))

    def insert_positions(self, records, timestamp):
        self._batch_execute([self._stops_to_sql(self.insert_string, r) for r in records])


class MySQL(DB):
    _create_table_string = '''CREATE TABLE IF NOT EXISTS positions (pkey integer primary key auto_increment, lat real, lon real, ar varchar(20), bid varchar(20), c varchar(20), cars varchar(20), consist varchar(20), d varchar(20), dd varchar(20), dn varchar(20), fs varchar(255), id varchar(20), m varchar(20), op varchar(20), pd varchar(20), pdRtpiFeedName varchar(20), pid varchar(20), rt varchar(20), rtRtpiFeedName varchar(20), rtdd varchar(20), rtpiFeedName varchar(20), run varchar(20), wid1 varchar(20), wid2 varchar(20), timestamp varchar(255))'''

    _insert_string = 'INSERT INTO positions VALUES(NULL, %f, %f, "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s")'

    def __init__(self, db_name, db_user, db_password, db_host='127.0.0.1'):
        DB.__init__(self, MySQL._insert_string)
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self._setup_db()

    def _setup_db(self):
        self.conn = connection.MySQLConnection(user=self.db_user, password=self.db_password, host=self.db_host)
        self._execute('CREATE DATABASE IF NOT EXISTS %s;' % self.db_name)
        self.conn.database = self.db_name

        try:
            self._execute(MySQL._create_table_string)
        except mysql.connector.Error as err:
            pass

