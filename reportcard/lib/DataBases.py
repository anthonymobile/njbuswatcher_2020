
####################################################
BusDB
####################################################


from mysql.connector import connection

_columns = ['lat','lon','ar','bid','c','cars','consist','d','dd','dn','fs','id','m','op','pd','pdRtpiFeedName','pid','rt','rtRtpiFeedName','rtdd','rtpiFeedName','run','wid1','wid2']

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
        self._batch_execute([_bus_to_sql(self.insert_string, r, timestamp) for r in records])

    def fetch_records(self,query):
        cursor = self.conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        return rows


class MySQL(DB):
    _create_table_string = '''CREATE TABLE IF NOT EXISTS positions (pkey integer primary key auto_increment, lat real, lon real, ar varchar(20), bid varchar(20), c varchar(20), cars varchar(20), consist varchar(20), d varchar(20), dd varchar(255), dn varchar(20), fs varchar(255), id varchar(20), m varchar(20), op varchar(20), pd varchar(255), pdRtpiFeedName varchar(20), pid varchar(20), rt varchar(20), rtRtpiFeedName varchar(20), rtdd varchar(20), rtpiFeedName varchar(20), run varchar(20), wid1 varchar(20), wid2 varchar(20), timestamp varchar(255),
                INDEX (rt),
                INDEX (run) 
    )'''

    _insert_string = 'INSERT INTO positions VALUES(NULL, %f, %f, "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s")'

    def __init__(self, db_name, db_user, db_password, db_host):
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
        except:
            pass


####################################################
BusRouteLogsDB
####################################################

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

        create_table_string = '''CREATE TABLE IF NOT EXISTS %s (pkey integer primary key auto_increment, lat real, lon real, bid varchar(20), cars varchar(20), consist varchar(20), d varchar(20), dip varchar(20), dn varchar(20), fs varchar(255), id varchar(20), m varchar(20), op varchar(20), pd varchar(255), pdRtpiFeedName varchar(20), pid varchar(20), rt varchar(20), rtRtpiFeedName varchar(20), rtdd varchar(20), rtpiFeedName varchar(20), run varchar(20), wid1 varchar(20), wid2 varchar(20), timestamp varchar(255),
                INDEX (bid),
                INDEX (rt),
                INDEX (run) 
                )''' % table_name


        try:
            self.conn = connection.MySQLConnection(user=self.db_user, password=self.db_password, host=self.db_host)
            self._execute('CREATE DATABASE IF NOT EXISTS %s;' % self.db_name)
            self.conn.database = self.db_name
            self._execute(create_table_string)
        except Error as err:
            print('something went wrong with mysql')
            sys.exit()
            pass


####################################################
StopsDB
####################################################


from mysql.connector import connection
from mysql.connector import Error
import sys

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

    # UNTESTED
    def fetch_records(self,query):
        cursor = self.conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        return rows


class MySQL(DB):

    def __init__(self, db_name, db_user, db_password, db_host,route):

        table_name = 'stop_approaches_log_' + route


        insert_string = 'INSERT INTO '+ table_name + ' VALUES(NULL, "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s")'

        DB.__init__(self, insert_string)
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self._setup_db(table_name)

    def _setup_db(self,table_name):

        create_table_string = '''CREATE TABLE IF NOT EXISTS %s (pkey integer primary key auto_increment, cars varchar(20), consist varchar(20), fd varchar(255), m varchar(20), name varchar(20), pt varchar(20), rd varchar(20), rn varchar(20), scheduled varchar(20), stop_id varchar(20), stop_name varchar(255), v varchar(20), timestamp varchar(255),
                INDEX (rd),
                INDEX (stop_id),
                INDEX (v) 
                )'''  % table_name

        try:
            self.conn = connection.MySQLConnection(user=self.db_user, password=self.db_password, host=self.db_host)
            self._execute('CREATE DATABASE IF NOT EXISTS %s;' % self.db_name)
            self.conn.database = self.db_name

            self._execute(create_table_string)

        except Error as err:
            print('something went wrong with mysql')
            sys.exit()
            pass


####################################################
TripsDB
####################################################

from mysql.connector import connection
from mysql.connector import Error
import sys

_columns = ['id','date','lat','lon','timestamp','run','stop_id','stop_name','dd','distance']



def _stops_to_sql(format_string, stop, timestamp):

    for var in _columns:
        if not hasattr(stop, var):
            setattr(stop, var, '')

    return format_string % (stop.id, stop.date, stop.lat, stop.lon, str(timestamp),
                            stop.stop_id, stop.stop_name, stop.distance)



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
        self._batch_execute([_stops_to_sql(self.insert_string, r, timestamp) for r in records]) # problem is im trying to feed this a dataframe!!!!

    # UNTESTED
    def fetch_records(self,query):
        cursor = self.conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        return rows


class MySQL(DB):

    def __init__(self, db_name, db_user, db_password, db_host,route):

        table_name = 'triplog_' + route


        insert_string = 'INSERT INTO '+ table_name + ' VALUES(NULL, "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s","%s")'

        DB.__init__(self, insert_string)
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self._setup_db(table_name)

    def _setup_db(self,table_name):

        create_table_string = '''CREATE TABLE IF NOT EXISTS %s (pkey integer primary key auto_increment, id varchar(20), date varchar(20), lat varchar(255), lon varchar(20), timestamp varchar(255), run varchar(20), stop_id varchar(20), stop_name varchar(255), dd varchar(20), distance varchar(20),
                INDEX (id),
                INDEX (stop_id),
                INDEX (date) 
                )'''  % table_name


        try:
            self.conn = connection.MySQLConnection(user=self.db_user, password=self.db_password, host=self.db_host)
            self._execute('CREATE DATABASE IF NOT EXISTS %s;' % self.db_name)
            self.conn.database = self.db_name

            self._execute(create_table_string)

        except Error as err:
            print('something went wrong with mysql')
            sys.exit()
            pass
