
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

