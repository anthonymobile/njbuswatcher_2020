import sqlite3
import pandas as pd
import StopsDB

_dict1 = {
  'nj': 'http://mybusnow.njtransit.com/bustime/map/'
}

_dict2 = {
  'all_buses': 'getBusesForRouteAll.jsp',
  'routes': 'getRoutePoints.jsp',
  'pattern_points': 'getPatternPoints.jsp',
  'stop_predictions': 'getStopPredictions.jsp',
  'bus_predictions': 'getBusPredictions.jsp',
  'buses_for_route': 'getBusesForRoute.jsp',
  'schedules': 'schedules.jsp',
  'time_and_temp': 'getTimeAndTemp.jsp',
  'route_directions_xml':  'routeDirectionStopAsXML',
}


def _command1(source, func, **kwargs):
    result = _sources[source] + _api[func]
    params = ''
    for k, v in kwargs.items():
        params = params + k + '=' + str(v) + '&'
    if params:
        result += '?' + params[:-1]
    return result

def _command2(tree, key, default=''):
    res = tree.find(key)
    if res is not None:
        return res.text
    return default

class KeyValueData:
    def __init__(self, **kwargs):
        self.name = 'KeyValueData'
        for k, v in kwargs.items():
            setattr(self, k, v)

    def add_kv(self, key, value):
        setattr(self, key, value)

    def __repr__(self):
        line = []
        for prop, value in vars(self).iteritems():
            line.append((prop, value))
        line.sort(key=lambda x: x[0])
        out_string = ' '.join([k + '=' + str(v) for k, v in line])
        return self.name + '[%s]' % out_string


class ReportCard(source, route, stop, period):

    # parent class has stuff common to both Route and Stop reports


    class RouteReport

    # should these be children of the Route? why not?
    class StopReport(KeyValueData):
        def __init__(self):
            KeyValueData.__init__(self)
            self.name = 'Path'
            self.points = []
            self.id = ''
            self.d = ''
            self.dd = ''

            # returns a object consisting of
            # all the content that will get dispalyed in the template
            #   dict that will get iterated and or otherwise parsed into the template for display




# sample class code

# class ReportSimple(KeyValueData):
#     def __init__(self, **kwargs):
#         KeyValueData.__init__(self, **kwargs)
#         self.name = 'Bus'
#
# class ReportComplex(KeyValueData):
#
#     class Path(KeyValueData):
#         def __init__(self):
#             KeyValueData.__init__(self)
#             self.name = 'Path'
#             self.points = []
#             self.id = ''
#             self.d = ''
#             self.dd = ''
#
#     class Point:
#         def __init__(self):
#             self.lat = ''
#             self.lon = ''
#             self.d = ''
#
#     class Stop:
#         def __init__(self):
#             self.identity = ''
#             self.st = ''
#             self.lat = ''
#             self.lon = ''
#             self.d = ''
#

def common_function(source, function, **kwargs):
    import urllib2
    data = urllib2.urlopen(_gen_command(source, function, **kwargs)).read()
    return data

def another_common_function(source, function, **kwargs):
    import urllib2
    data = urllib2.urlopen(_gen_command(source, function, **kwargs)).read()
    return data

# database interactions--------------------------


### get list of all stops for 'route' currently observed in the entire database
def get_stoplist(route):

    (conn, db) = db_setup(route)

    stoplist_query = (
            'SELECT stop_id FROM stop_predictions WHERE rd = %s GROUP BY stop_id;' % route)
    stoplist = pd.read_sql_query(stoplist_query, conn)

    return stoplist['stop_id']


#
# data transformations
#

# trim the microseconds off the timestamp and convert it to datetime format
def timestamp_fix(data):

    data['timestamp'] = data['timestamp'].str.split('.').str.get(0)
    # data['timestamp'] = pd.to_datetime(data['timestamp'])
    # data = data.set_index('timestamp', drop=False)
    data = data.set_index(pd.DatetimeIndex(data['timestamp']), drop=False)

    return data


#
# data views
#

# for a single stop, all buses seen in history
def render_arrivals_history_1stop(source, route, stop):

    # get a clean df
    (conn, db) = db_setup(route)
    arrival_query = (
                'SELECT * FROM stop_predictions WHERE (rd = %s AND pt = "APPROACHING" AND stop_id= %s ) ORDER BY stop_id,timestamp;' % (route, stop))
    df = pd.read_sql_query(arrival_query, conn)
    df = timestamp_fix(df)


    # insert code derived from nb-new_stopwatcher_data_structure.ipynb

    arrivals_history_1stop = []

    return arrivals_history_1stop



# def render_arrivals_hourly_mean(source, route, stoplist):
#
#     (conn, db) = db_setup(route)
#
#     arrival_query = (
#             'SELECT * FROM stop_predictions WHERE (rd = %s AND pt = "APPROACHING") ORDER BY stop_id,timestamp;' % route)
#
#     df = pd.read_sql_query(arrival_query, conn)
#
#     df = timestamp_fix(df)
#
#     arrivals_history_hourly = []
#
#     for s in stoplist:
#
#         df_stop = df.loc[df.stop_id == s]
#
#         df_stop['delta'] = df_stop['timestamp'] - df_stop['timestamp'].shift(1)
#
#         # resample hourly average
#         # need to convert delta to numeric type first per...
#         # https://stackoverflow.com/questions/44616546/finding-the-mean-and-standard-deviation-of-a-timedelta-object-in-pandas-df
#
#         df_stop['delta_int'] = df_stop['delta'].values.astype(np.int64)
#
#         for hour in df_stop.delta_int.resample('H').mean().iteritems():
#             dict_ins = {}
#             dict_ins['stop_id'] = s
#             dict_ins['hour_top'] = hour[0]
#             dict_ins['avg_interval'] = hour[1]
#             arrivals_history_hourly.append(dict_ins)
#
#     return arrivals_history_hourly
#
#
# def render_arrivals_history_full(source, route, stoplist):
#
#     (conn, db) = db_setup(route)
#
#     arrival_query = (
#                 'SELECT * FROM stop_predictions WHERE (rd = %s AND pt = "APPROACHING") ORDER BY stop_id,timestamp;' % route)
#     df = pd.read_sql_query(arrival_query, conn)
#     df = timestamp_fix(df)
#     arrivals_history_full = []
#
#     for s in stoplist:
#         df_stop = df.loc[df.stop_id == s]
#
#         df_stop['delta'] = df_stop['timestamp'] - df_stop['timestamp'].shift(1)
#
#
#         for index, row in df_stop.iterrows():
#             dict_ins = {}
#             dict_ins['stop_id'] = row['stop_id']
#             dict_ins['v'] = row['v']
#             dict_ins['timestamp'] = row['timestamp']
#             try:
#                 dict_ins['delta'] = row['delta'].seconds
#             except:
#                 dict_ins['delta'] = row['delta']
#             arrivals_history_full.append(dict_ins)
#
#     return arrivals_history_full
