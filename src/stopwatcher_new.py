########################################################
#
#
#
# transpose here from Jupyter when its working
#
#
#
########################################################

import time

from buses.reportcard_helpers import *

def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        if 'log_time' in kw:
            name = kw.get('log_name', method.__name__.upper())
            kw['log_time'][name] = int((te - ts) * 1000)
        else:
            print '%r  %2.2f ms' % (method.__name__, (te - ts) * 1000)
        return result

    return timed


@timeit
def make_history(df):
    # THIS IS WAYYYYYYY FASTER !!!

    # history data structure = assign every row in df to a dict keyed to unique vehicle/stop_id instance
    # {
    #  5403_20640: [row1, row15, ...]
    #  5704_20933: [row2, row37, ...]
    # }

    from collections import defaultdict
    history = defaultdict(list)

    for index, row in df.iterrows():
        key = row['v'] + '_' + row['stop_id']
        history[key].append(row)

    # sort them and slice them

    keepers = defaultdict(list)
    discards = defaultdict(list)

    # iterate over the dict
    for key_copy, arrivals in history.iteritems():
        # sort each arrival list
        arrivals.sort(key=lambda x: x.timestamp)

        #
        #
        # NEED TO GROUPBY ONES THAT HAVE THE SAME GENERAL ARRIVAL WINDOW
        #
        # PROBLEM WITH BELOW IS THAT IT DOESNT WORK WHEN WE HAVE A FULL HISTORY
        # BECAUSE IT DOESNT DETECT EVENTS? e.g. VEHICLE-STOP COMBINATIONS ARE NOT UNIQUE FOR MORE THAN A FEW HOURS
        #
        #

        # put last row in keepers
        keepers[key_copy].append(arrivals[-1])

        # put everything else in discards
        discards[key_copy].append(arrivals[:-1])

        return keepers, discards

def main():

    source = 'nj'
    route = 119

    (conn, db) = db_setup(route)

    # only get buses APPROACHING A STOP
    arrival_query = ('SELECT * FROM stop_predictions \
                    WHERE (rd = %s AND pt = "APPROACHING") \
                    ORDER BY timestamp;' % route)
    # arrival_query = ('SELECT * FROM stop_predictions;')

    df = pd.read_sql_query(arrival_query, conn)
    print df.head(5)

    df = timestamp_fix(df)

    df.groupby(['v', 'stop_id'])

    (keepers, discards) = make_history(df)
    print keepers
    print discards


if __name__ == "__main__":
    main()
