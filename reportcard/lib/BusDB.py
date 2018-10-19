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
    _create_table_string = '''CREATE TABLE IF NOT EXISTS positions (pkey integer primary key auto_increment, lat real, lon real, ar varchar(20), bid varchar(20), c varchar(20), cars varchar(20), consist varchar(20), d varchar(20), dd varchar(20), dn varchar(20), fs varchar(255), id varchar(20), m varchar(20), op varchar(20), pd varchar(255), pdRtpiFeedName varchar(20), pid varchar(20), rt varchar(20), rtRtpiFeedName varchar(20), rtdd varchar(20), rtpiFeedName varchar(20), run varchar(20), wid1 varchar(20), wid2 varchar(20), timestamp varchar(255),
                INDEX (rt),
                INDEX (run), 
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
