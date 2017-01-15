import os
import sqlite3
from mysql.connector import connection 

_columns = [ 'lat',
 'lon',
 'ar',
 'bid',
 'c',
 'cars',
 'consist',
 'd',
 'dd',
 'dn',
 'fs',
 'id',
 'm',
 'op',
 'pd',
 'pdRtpiFeedName',
 'pid',
 'rt',
 'rtRtpiFeedName',
 'rtdd',
 'rtpiFeedName',
 'run',
 'wid1',
 'wid2' ]

def _bus_to_sql(format_string, bus, timestamp):
    for var in _columns: 
        if not hasattr(bus, var):
            if var == 'lat' or var == 'lon':
                setattr(bus, var, 0.0)
            else: 
                setattr(bus, var, '')
  
    return format_string % (float(bus.lat), float(bus.lon), bus.ar, bus.bid, bus.c, bus.cars, bus.consist, bus.d, bus.dd, bus.dn, bus.fs, bus.id, bus.m, bus.op, bus.pd, bus.pdRtpiFeedName, bus.pid, bus.rt, bus.rtRtpiFeedName, bus.rtdd, bus.rtpiFeedName, bus.run, bus.wid1, bus.wid2, str(timestamp)) 

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

    def insert_positions(self, buses, timestamp):
        import ipdb
        ipdb.set_trace()
        self._batch_execute([_bus_to_sql(self.insert_string, b, timestamp) for b in buses])

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

class MySQL(DB):
    _create_table_string = '''CREATE TABLE IF NOT EXISTS positions (pkey integer primary key auto_increment, lat real, lon real, ar varchar(255), bid varchar(255), c varchar(255), cars varchar(255), consist varchar(255), d varchar(255), dd varchar(255), dn varchar(255), fs varchar(255), id varchar(255), m varchar(255), op varchar(255), pd varchar(255), pdRtpiFeedName varchar(255), pid varchar(255), rt varchar(255), rtRtpiFeedName varchar(255), rtdd varchar(255), rtpiFeedName varchar(255), run varchar(255), wid1 varchar(255), wid2 varchar(255), timestamp varchar(255))'''
 
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
