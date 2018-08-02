import pandas as pd
import StopsDB,BusRouteLogsDB

# common - UNUSED
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
def common_function(source, function, **kwargs):
    import urllib2
    data = urllib2.urlopen(_gen_command(source, function, **kwargs)).read()
    return data
def another_common_function(source, function, **kwargs):
    import urllib2
    data = urllib2.urlopen(_gen_command(source, function, **kwargs)).read()
    return data

# common - BY ME
def timestamp_fix(data): # trim the microseconds off the timestamp and convert it to datetime format

    data['timestamp'] = data['timestamp'].str.split('.').str.get(0)
    # data['timestamp'] = pd.to_datetime(data['timestamp'])
    # data = data.set_index('timestamp', drop=False)
    data = data.set_index(pd.DatetimeIndex(data['timestamp']), drop=False)

    return data

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

# main classes
class Report: #---------------------------------------------
    def __init__(self, source, route, stop, period): # parent class has stuff common to both Route and Stop reports
        self.source = source
        self.route = route
        self.stop = stop
        self.period = period
        #self.pagetitle
        #self.fieldx

    class StopReport: #---------------------------------------------
        # creates a object with properties that contain all the content that will be
        # rendered by the template
        # e.g. dicts or lists that will get iterated over into tables for display

        def __init__(self,route):
            self.route=route
            self.db = StopsDB.MySQL('buses', 'buswatcher', 'njtransit', '127.0.0.1', self.route)
            self.conn = self.db.conn
            self.table_name = 'stop_approaches_log_' + route

        def get_approaches(self,stop,period):

            if period == "daily":
                approach_query = ('SELECT * FROM %s WHERE (stop_id= %s AND (DATE(`timestamp`) = CURDATE()) ORDER BY stop_id,timestamp;' % (self.table_name,stop))

            elif period=="weekly":
                approach_query = ('SELECT * FROM %s WHERE (stop_id= %s AND (YEARWEEK(`timestamp`, 1) = YEARWEEK(CURDATE(), 1))) ORDER BY stop_id,timestamp;' % (self.table_name,stop))

            elif period=="history":
                approach_query = ('SELECT * FROM %s WHERE stop_id= %s) ORDER BY stop_id,timestamp;' % (self.table_name,stop))

            df = pd.read_sql_query(arrival_query, self.conn)
            df = timestamp_fix(df)

            # return raw list of approaches
            self.approach_results = []
            for index, row in df.iterrows():
                dict_ins = {}
                dict_ins['stop_id'] = row['stop_id']
                dict_ins['v'] = row['v']
                dict_ins['timestamp'] = row['timestamp']
                self.approach_results.append(dict_ins)
            return
