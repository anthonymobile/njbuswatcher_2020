import os
import datetime
import xml.etree.ElementTree

# API like: https://github.com/harperreed/transitapi/wiki/Unofficial-Bustracker-API

_sources = {
  'nj': 'http://mybusnow.njtransit.com/bustime/map/'
}

_api = {
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

# parsers done for all_buses, routes, stop_predictions
# ignored: time_and_temp
# not available / not fully documented: schedules (not sure what the right kwargs are, agency=1 & route=87 ?)


def _gen_command(source, func, **kwargs):
    result = _sources[source] + _api[func]
    params = ''
    for k, v in kwargs.items():
        params = params + k + '=' + str(v) + '&'
    if params:
        result += '?' + params[:-1]
    return result

def _cond_get_single(tree, key, default=''):
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

class Bus(KeyValueData):
    def __init__(self, **kwargs):
        KeyValueData.__init__(self, **kwargs)
        self.name = 'Bus'

class Route(KeyValueData):

    class Path(KeyValueData):
        def __init__(self):
            KeyValueData.__init__(self)
            self.name = 'Path'
            self.points = []
            self.id = ''
            self.d = ''
            self.dd = ''

    class Point:
        def __init__(self):
            self.lat = ''
            self.lon = ''
            self.d = ''

    class Stop:
        def __init__(self):
            self.identity = ''
            self.st = ''
            self.lat = ''
            self.lon = ''
            self.d = ''

    def __init__(self):
        KeyValueData.__init__(self)
        self.name = 'route'
        self.identity = ''
        self.paths = []

class StopPrediction(KeyValueData):
    def __init__(self, **kwargs):
        KeyValueData.__init__(self, **kwargs)
        self.name = 'StopPrediction' 

def parse_stopprediction_xml(data):
    results = []
    e = xml.etree.ElementTree.fromstring(data)

    for atype in e.findall('pre'):
        fields = {}
        for field in atype.getchildren():
            if field.tag not in fields and hasattr(field, 'text'):
                if field.text is None:
                    fields[field.tag] = ''
                    continue
                fields[field.tag] = field.text

        results.append(StopPrediction(**fields))

        # go through and append the stop id and name to every result
        stop_id = e.find('id').text
        stop_nm = e.find('nm').text
        for prediction in results:
            prediction.stop_id = stop_id 
            prediction.stop_name = stop_nm 
            # and split the integer out of the prediction
            prediction.pt = prediction.pt.split(' ')[0]
    return results
    
# end of stops add

def parse_bus_xml(data):
    results = []

    e = xml.etree.ElementTree.fromstring(data)
    for atype in e.findall('bus'):
        fields = {}
        for field in atype.getchildren():
            if field.tag not in fields and hasattr(field, 'text'):
                if field.text is None:
                    fields[field.tag] = ''
                    continue
                fields[field.tag] = field.text

        results.append(Bus(**fields))
    return results


def parse_route_xml(data):

    routes = list()

    route = Route()

    e = xml.etree.ElementTree.fromstring(data)
    for child in e.getchildren():

        if len(child.getchildren()) == 0:
            if child.tag == 'id':
                route.identity = child.text
            else:
                route.add_kv(child.tag, child.text)

        if child.tag == 'pas':

            for pa in child.findall('pa'):

                path = Route.Path()

                for path_child in pa.getchildren():
                    if len(path_child.getchildren()) == 0:
                        if path_child.tag == 'id':
                            path.id = path_child.text
                        elif path_child.tag == 'd':
                            path.d = path_child.text
                        elif path_child.tag == 'dd':
                            path.dd = path_child.text
                        else:
                            path.add_kv(path_child.tag, path_child.text)
                    elif path_child.tag == 'pt':
                        pt = path_child
                        stop = False
                        for bs in pt.findall('bs'):
                            stop = True
                            _stop_id = _cond_get_single(bs, 'id')
                            _stop_st = _cond_get_single(bs, 'st')
                            break

                        p = None
                        if not stop:
                            p = Route.Point()
                        else:
                            p = Route.Stop()
                            p.identity = _stop_id
                            p.st = _stop_st

                        p.d = path.d
                        p.lat = _cond_get_single(pt, 'lat')
                        p.lon = _cond_get_single(pt, 'lon')

                        path.points.append(p) # <------ dont append to same list each time

                route.paths.append(path)

                routes.append(route.paths)

            break

    return routes

def get_xml_data(source, function, **kwargs):
    import urllib2
    data = urllib2.urlopen(_gen_command(source, function, **kwargs)).read()
    return data


def get_xml_data_save_raw(source, function, raw_dir, **kwargs):
    data = get_xml_data(source, function, **kwargs)
    if not os.path.exists(raw_dir):
        os.makedirs(raw_dir)

    now = datetime.datetime.now()
    handle = open(raw_dir + '/' + now.strftime('%Y%m%d.%H%M%S') + '.' + source + '.xml', 'w')
    handle.write(data)
    handle.close()
    return data


def parse_bus_xml_file(fname):
    return parse_bus_xml(open(fname, 'r').read())
