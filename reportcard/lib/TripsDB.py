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
