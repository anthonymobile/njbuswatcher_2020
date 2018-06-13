#!/usr/bin/python

# fetches the NJT statewide bus feed and dumps it to sqlite
# cron it every minute or 10 seconds or daemon-ize it?


import sys
import argparse
import datetime

from lib import BusDB, Buses


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', dest='source', default='nj', help='source name')
    parser.add_argument('--save-raw', dest='raw', default=None, required=False, help='directory to save the raw data to')

    # sqlite backend - just requires write privs on the file
    subparsers = parser.add_subparsers() 
    sqlite_parser = subparsers.add_parser('sqlite')
    sqlite_parser.add_argument('--sqlite-file', dest='sqlite_file', required=True, help='location of the sqlite file', default=None)

    # script cannot create database
    # requirements: database already exists, or the user specified has CREATE DATABASE privs
    mysql_parser = subparsers.add_parser('mysql') 
    mysql_parser.add_argument('--db-name', dest='db_name', required=True, help='name of the mysql database')
    mysql_parser.add_argument('--db-user', dest='db_user', required=True, help='name of the mysql user')
    mysql_parser.add_argument('--db-pw', dest='db_password', required=False, help='name of the mysql password')
    mysql_parser.add_argument('--db-host', dest='db_host', required=False, default='127.0.0.1', help='host of the mysql database')

    args = parser.parse_args()

    if args.source not in Buses._sources:
        print args.source + ' is not a valid source.  Valid sources=' + str(Buses._sources.keys())
        sys.exit(-1)
   
    if hasattr(args, 'db_name'):
        db = BusDB.MySQL(args.db_name, args.db_user, args.db_password, args.db_host)
    elif hasattr(args, 'mongo_name'):
        db = BusDB.Mongo(args.mongo_name)
    elif hasattr(args, 'sqlite_file'): 
        db = BusDB.SQLite(args.sqlite_file)
    else:
        print 'cannot deduce database type'
        sys.exit(-2)

    now = datetime.datetime.now()
    if args.raw:
        bus_data = Buses.parse_bus_xml(Buses.get_xml_data_save_raw(args.source, 'all_buses', args.raw))
    else:
        bus_data = Buses.parse_bus_xml(Buses.get_xml_data(args.source, 'all_buses'))
    db.insert_positions(bus_data, now)

if __name__ == "__main__":
    main()
