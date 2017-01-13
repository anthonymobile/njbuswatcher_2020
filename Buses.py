import os
import datetime
import xml.etree.ElementTree

#API like: https://github.com/harperreed/transitapi/wiki/Unofficial-Bustracker-API

_sources = {
  'nj': 'http://mybusnow.njtransit.com/bustime/map/'
}

_api = { 
  'all_buses': 'getBusesForRouteAll.jsp',
  'routes': 'getRoutePoints.jsp',
  'pattern_points': 'getPatternPoints.jsp',
  'stop_predicitons': 'getStopPredictions.jsp',
  'bus_predictions': 'getBusPredictions.jsp',
  'buses_for_route': 'getBusesForRoute.jsp',
  'buses_for_route_all': 'getBusesForRouteAll.jsp',
  'schedules': 'schedules.jsp',
  'time_and_temp': 'getTimeAndTemp.jsp',
  'route_directions_xml':  'routeDirectionStopAsXML',
}

def _gen_command(source, func, **kwargs):
  result = _sources[source] + _api[func] 
  params = ''
  for k,v in kwargs.items():
    params = params + k + '=' + v + '&'
  if params:
    result += '?' + params[:-1]
  return result

class Bus:
  def __init__(self, **kwargs):
     for k,v in kwargs.items():
         setattr(self, k, v)

  def __repr__(self):
     line = []
     for prop,value in vars(self).iteritems():
       line.append((prop,value))
     line.sort(key=lambda x : x[0])
     out_string = ' '.join([k+'='+v for k,v in line]) 
     return 'bus[%s]' % out_string

def parse_bus_xml(data):
    results = []

    e = xml.etree.ElementTree.fromstring(data)
    for atype in e.findall('bus'):
        fields = { }
        for field in atype.getchildren():
            if field.tag not in fields and hasattr(field, 'text'):
                if field.text is None:
                    fields[field.tag] = ''
                    continue
                fields[field.tag] = field.text

        results.append(Bus(**fields))
    return results

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
    return parse_bus_xml(open(fname,'r').read())
