
import argparse
from lib.reportcard_helpers import *

source = 'nj'
route = 87
(conn, db) = db_setup(route)
arrival_query = ('SELECT * FROM stop_predictions WHERE (rd = %s AND pt = "APPROACHING") ORDER BY timestamp;' % route)
df = pd.read_sql_query(arrival_query, conn)
df = timestamp_fix(df)

keys = df.groupby(['v','stop_id']).groups.keys()
history=[]
for i,k in enumerate(keys):
    v = k[0]
    stop_id = k[1]
    for index,row in df.iterrows():
        if ( row['v']== v ) and ( row['stop_id']== stop_id):
            history.append(row)
        else:
            pass
    

df_final = pd.concat([x for x in history],axis=1)
df_final.T


"""
old code

# this python app should run cron as a cron job
# grabs the current arrivals for every stop on a source, route

# all it does is talk to the database. never talks to flask

#
# python stopwatcher.py -s nj -r 87
#


import argparse, sys
from lib.reportcard_helpers import *


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', dest='source', required=True, default='nj', help='source name')
    parser.add_argument('-r', '--route', dest='route', required=True, help='route # ')
    args = parser.parse_args()

    fetch_arrivals(args.source, args.route)

if __name__ == "__main__":
    main()


# TO DO
# 1 rewrite to use mysql
# 2 deploy to webster.hopto.org

"""

