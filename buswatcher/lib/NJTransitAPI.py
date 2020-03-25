import os
import time
import datetime
import xml.etree.ElementTree
import geojson

from .CommonTools import get_config_path

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


def _gen_command(source, func, **kwargs):
    result = _sources[source] + _api[func]
    params = ''
    for k, v in list(kwargs.items()):
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
        for k, v in list(kwargs.items()):
            setattr(self, k, v)

    def add_kv(self, key, value):
        setattr(self, key, value)

    def __repr__(self):
        line = []
        for prop, value in vars(self).items():
            line.append((prop, value))
        line.sort(key=lambda x: x[0])
        out_string = ' '.join([k + '=' + str(v) for k, v in line])
        return self.name + '[%s]' % out_string

    def to_dict(self):
        line = []
        for prop, value in vars(self).items():
            line.append((prop, value)) # list of tuples
        line.sort(key=lambda x: x[0])
        out_dict = dict()
        for l in line:
            out_dict[l[0]]=l[1]
        return out_dict

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


#
# parsers for specific API calls
#
# parsers done for all_buses, routes, stop_predictions
# ignored: time_and_temp
# not available / not fully documented: schedules (not sure what the right kwargs are, agency=1 & route=87 ?)


def parse_xml_getStopPredictions(data):
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

def parse_xml_getBusesForRouteAll(data):
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

    return clean_buses(results)


# http://mybusnow.njtransit.com/bustime/map/getBusesForRoute.jsp?route=119
def parse_xml_getBusesForRoute(data):
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
    return clean_buses(results)


def clean_buses(buses):
    buses_clean = []
    for bus in buses:
        if bus.run.isdigit() is True:  # removes any buses with non-number run id, and this should populate throughout the whole project
            if bus.rt.isdigit() is True:  # removes any buses with non-number route id, and this should populate throughout the whole project
                buses_clean.append(bus)

    return buses_clean

#
# # http://mybusnow.njtransit.com/bustime/map/getBusPredictions?bus=3452
# def parse_xml_getBusPredictions(data): # dont think this API endpoint works on NJT
#     results = ''
#     return results


def validate_xmldata(rd):

    # load the route file
    infile = (get_config_path() + 'route_geometry/' + str(rd) + '.xml')
    with open(infile, 'rb') as f:
        e = xml.etree.ElementTree.fromstring(f.read())
        for child in e.getchildren():
            if child.tag == 'pas':
                if len(child.findall('pa')) == 0:
                    print('Route not valid')
                    return False
                elif len(child.findall('pa')) > 0:
                    return True


# http://mybusnow.njtransit.com/bustime/map/getRoutePoints.jsp?route=119
def parse_xml_getRoutePoints(data):

    coordinates_bundle=dict()
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
                routes.append(route)
            break



    # dump waypoint coordinates to geojson
    waypoint_coordinates=[]
    for point in routes[0].paths[0].points:
        # undo this for plot.ly
        # reversed lon, lat for some reason for MapBox
        # waypoint_coordinates.append((float(point.lon),float(point.lat)))
        waypoint_coordinates.append((float(point.lat),float(point.lon)))
    route_plot = geojson.LineString(waypoint_coordinates)
    waypoints_geojson = geojson.dumps(route_plot, sort_keys=True)

    # dump stop coordinates to geojson
    stops_coordinates = []
    for point in routes[0].paths[0].points:
        if isinstance(point, Route.Stop):
            stops_coordinates.append((float(point.lon), float(point.lat)))
    stops_plot = geojson.MultiPoint(stops_coordinates)
    stops_geojson = geojson.dumps(stops_plot, sort_keys=True)

    coordinates_bundle['waypoints_coordinates'] = waypoint_coordinates
    coordinates_bundle['stops_coordinates'] = stops_coordinates
    coordinates_bundle['waypoints_geojson'] = waypoints_geojson
    coordinates_bundle['stops_geojson'] = stops_geojson

    return routes, coordinates_bundle

def get_xml_data(source, function, **kwargs):
    import urllib.request
    tries = 1
    while True:
        try:
            data = urllib.request.urlopen(_gen_command(source, function, **kwargs)).read()
            if data:
                break
        except:

            print (str(tries) + '/12 cant connect to NJT API... waiting 5s and retry')
            if tries < 12:
                tries = tries + 1
                time.sleep(5)
            else:
                print('failed trying to connect to NJT API for 1 minute, giving up')
                return

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
