from mysql.connector import connection
from mysql.connector import Error
import sys

_columns = ['lat','lon','bid','cars','consist','d','dip','dn','fs','id','m','op','pd','pdRtpiFeedName','pid','rt','rtRtpiFeedName','rtdd','rtpiFeedName','run','wid1','wid2']

def _bus_to_sql(format_string, bus, timestamp):
    for var in _columns:
        if not hasattr(bus, var):
            if var == 'lat' or var == 'lon':
                setattr(bus, var, 0.0)
            else:
                setattr(bus, var, '')

    return format_string % (
    float(bus.lat), float(bus.lon), bus.bid, bus.cars, bus.consist, bus.d, bus.dip, bus.dn, bus.fs, bus.id, bus.m, bus.op, bus.pd, bus.pdRtpiFeedName, bus.pid, bus.rt, bus.rtRtpiFeedName, bus.rtdd, bus.rtpiFeedName, bus.run, bus.wid1, bus.wid2, str(timestamp))


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
        self._batch_execute([_bus_to_sql(self.insert_string, r, timestamp) for r in records])

    def fetch_records(self,query):
        cursor = self.conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        return rows


class MySQL(DB):

    def __init__(self, db_name, db_user, db_password, db_host, route):

        table_name = 'routelog_' + route

        insert_string = 'INSERT INTO '+ table_name + ' VALUES(NULL, %f, %f, "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s")'

        DB.__init__(self, insert_string)
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self._setup_db(table_name)

    def _setup_db(self,table_name):

        create_table_string = '''CREATE TABLE IF NOT EXISTS %s (pkey integer primary key auto_increment, lat real, lon real, bid varchar(20), cars varchar(20), consist varchar(20), d varchar(20), dip varchar(20), dn varchar(20), fs varchar(255), id varchar(20), m varchar(20), op varchar(20), pd varchar(20), pdRtpiFeedName varchar(20), pid varchar(20), rt varchar(20), rtRtpiFeedName varchar(20), rtdd varchar(20), rtpiFeedName varchar(20), run varchar(20), wid1 varchar(20), wid2 varchar(20), timestamp varchar(255))''' % table_name


        try:
            self.conn = connection.MySQLConnection(user=self.db_user, password=self.db_password, host=self.db_host)
            self._execute('CREATE DATABASE IF NOT EXISTS %s;' % self.db_name)
            self.conn.database = self.db_name
            self._execute(create_table_string)
        except Error as err:
            print 'something went wrong with mysql'
            sys.exit()
            pass
