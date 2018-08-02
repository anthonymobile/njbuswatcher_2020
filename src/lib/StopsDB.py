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

        table_name = 'stop_arrival_predictions_log_' + route


        insert_string = 'INSERT INTO '+ table_name + ' VALUES(NULL, "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s")'

        DB.__init__(self, insert_string)
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self._setup_db(table_name)

    def _setup_db(self,table_name):

        create_table_string = '''CREATE TABLE IF NOT EXISTS %s (pkey integer primary key auto_increment, cars varchar(20), consist varchar(20), fd varchar(255), m varchar(20), name varchar(20), pt varchar(20), rd varchar(20), rn varchar(20), scheduled varchar(20), stop_id varchar(20), stop_name varchar(255), v varchar(20), timestamp varchar(255))'''  % table_name

        try:
            self.conn = connection.MySQLConnection(user=self.db_user, password=self.db_password, host=self.db_host)
            self._execute('CREATE DATABASE IF NOT EXISTS %s;' % self.db_name)
            self.conn.database = self.db_name

            self._execute(create_table_string)

        except Error as err:
            print 'something went wrong with mysql'
            sys.exit()
            pass
