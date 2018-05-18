import os
import sqlite3
from mysql.connector import connection
import mongoengine as mongo
import datetime

_columns = ['cars','consist','fd','m','name','pt','rd','rn','scheduled','stop_id','stop_name','v']


def _stops_to_sql(format_string, stop, timestamp):
    # print dir(stop)
    for var in _columns:
        if not hasattr(stop, var):
            setattr(stop, var, '')

    return format_string % (stop.cars, stop.consist, stop.fd, stop.m, stop.name,
                            stop.pt, stop.rd, stop.rn, stop.scheduled, stop.stop_id,
                            stop.stop_name, stop.v, str(timestamp))


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
        self._batch_execute([_stops_to_sql(self.insert_string, r, timestamp) for r in records])


class SQLite(DB):
    _create_db_string = '''CREATE TABLE stop_predictions (pkey integer primary key autoincrement, cars text, consist text, fd text, m text, name text, pt text, rd text, rn text, scheduled text, stop_id text, stop_name text, v text, timestamp text)'''

    _insert_string = 'INSERT INTO stop_predictions VALUES(NULL, "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s")'

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
