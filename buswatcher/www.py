# todo 4 merge statewide branch back into new_localizer

# bus buswatcher v2.0
# june 2019 - by anthony@bitsandatoms.net

################################################
# VIP INSTANCE CONFIG
################################################

source_global='nj'
class Dummy():
    def __init__(self):
        self.routename = 'Jersey City'

################################################
# IMPORTS
################################################
import logging


from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
from flask import jsonify
from flask_cors import CORS, cross_origin

import buswatcher.lib.API as API
import buswatcher.lib.BusAPI as BusAPI
import buswatcher.lib.wwwAPI as wwwAPI


################################################
# ROUTE + APP CONFIG
################################################
from buswatcher.lib.RouteConfig import load_system_map

################################################
# APP
################################################
app = Flask(__name__, static_url_path='/static')
CORS(app, support_credentials=True)

################################################
# BOOTSTRAP
################################################
app.config.update(
    BOOTSTRAP_CDN_FORCE_SSL=True
)
Bootstrap(app)


################################################
# SETUP CACHE
################################################
from flask_caching import Cache
cache = Cache(app,config={'CACHE_TYPE': 'simple'})


################################################
# LOGGING
# per https://medium.com/@trstringer/logging-flask-and-gunicorn-the-manageable-way-2e6f0b8beb2f
################################################
if __name__ != "__main__":
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)


################################################
# STATIC ASSETS
################################################
from flask_assets import Bundle, Environment
bundles = {
    'route_css': Bundle(
        'css/theme.css',
        'css/theme.scss',
        output='gen/route.css'),
}
assets = Environment(app)
assets.register(bundles)

################################################
# HELPERS + DECORATORS
################################################

# def load_collection_routes(collection_url):
# # get list of routes in collection from route_config
#     d1, d2, collection_descriptions = load_config()
#     collection_metadata=dict()
#     for collection in collection_descriptions:
#         if collection['collection_url'] == collection_url:
#             collection_metadata = collection
#             break
#         else:
#             continue
#     return collection_metadata


################################################
# URLS
################################################

#-------------------------------------------------------------Statewide Index


def get_current_positions_db():
    # get list of all routes from system_map.routelist
    routelist=system_map.get_routelist()

    return

@app.route('/')
def displayIndex():

    # vehicle_data = BusAPI.parse_xml_getBusesForRouteAll(BusAPI.get_xml_data('nj','all_buses'))
    # vehicle_count = len(vehicle_data)
    # route_count = len(list(set([v.rt for v in vehicle_data])))

    vehicle_data, vehicle_count, route_count = API.current_buspositions_from_db_for_index()

    dummy= collection_descriptions
    routereport = Dummy() # setup a dummy routereport for the navbar
    return render_template('index.jinja2', collection_descriptions=collection_descriptions,  routereport=routereport, vehicle_count=vehicle_count, route_count=route_count)


#-------------------------------------------------------------City Index
@app.route('/<collection_url>')
def displayCollection(collection_url):

    # todo 3 better to find a less latency way to do this (with a db query)
    vehicles_now = API.get_positions_byargs(system_map, {'collection': collection_url, 'layer': 'vehicles'}, route_descriptions,
                             collection_descriptions)

    collection_description=collection_descriptions[collection_url]
    collection_description['number_of_active_vehicles'] = len(vehicles_now['features'])
    collection_description['number_of_active_routes'] = len(collection_descriptions[collection_url]['routelist'])

    route_report = Dummy()  # setup a dummy routereport for the navbar
    return render_template('collection.jinja2',collection_url=collection_url,collection_description=collection_description, route_descriptions=route_descriptions, period_descriptions=period_descriptions,routereport=route_report)


#-------------------------------------------------------------Route

@app.route('/<collection_url>/route/<route>/<period>')
def genRouteReport(collection_url,route, period):
    route_report = wwwAPI.RouteReport(system_map, route, period)

    return render_template('route.jinja2', collection_url=collection_url, collection_descriptions=collection_descriptions, route=route, period=period, period_descriptions=period_descriptions,routereport=route_report)

#------------------------------------------------------------Stop
@app.route('/<collection_url>/route/<route>/stop/<stop>/<period>')
def genStopReport(collection_url, route, stop, period):

    stop_report = wwwAPI.StopReport(system_map, route, stop, period)
    route_report = wwwAPI.RouteReport(system_map, route, period)
    predictions = BusAPI.parse_xml_getStopPredictions(BusAPI.get_xml_data('nj', 'stop_predictions', stop=stop, route='all'))

    return render_template('stop.jinja2',collection_url=collection_url, collection_descriptions=collection_descriptions, period_descriptions=period_descriptions, stop=stop, period=period, stopreport=stop_report, reportcard_routes=route_descriptions,predictions=predictions, routereport=route_report)

#-------------------------------------------------------------FAQ
@app.route('/faq')
def displayFAQ():
    routereport = Dummy() #  setup a dummy routereport for the navbar
    return render_template('faq.jinja2', route_definitions=route_descriptions, routereport=routereport)

#-------------------------------------------------------------API docs
@app.route('/api')
def displayAPI():
    routereport = Dummy() #  setup a dummy routereport for the navbar
    return render_template('api.jinja2', reportcard_routes=route_descriptions, routereport=routereport)


################################################
# API
################################################

# map layer geojson generator
#
# /api/v1/maps?

# for index map
#   layer=waypoints&rt=all              waypoints for ALL routes
#   layer=stops&rt=all              waypoints for ALL routes
#   layer=vehicles&rt=all               vehicles for ALL routes

# for collection map
#   layer=waypoints&collection=camden   waypoints for camden routes
#   layer=stops&collection=camden       stops for camden routes
#   layer=stops&collection=camden       vehicles for camden routes

# for route map
#   layer=waypoints&rt=87               waypoints for single route
#   layer=stops&rt=87                   stops for single route
#   layer=vehicles&rt=87                vehicles for single route

# for stop map
#   layer=stops&rt=87&stop_id=30189     stop for single stop
#   TK url for stop map waypoints
#   TK document url for stop map vehicles


# deprecated
# @app.route('/api/v1/maps')
# @cross_origin()
# def api_map_layer():
#     args=request.args
#
#     if args['layer'] == 'vehicles':
#         return jsonify(API.get_positions_byargs(system_map,args,route_descriptions,collection_descriptions))
#     else:
#         return jsonify(API.get_map_layers(system_map,args,route_descriptions,collection_descriptions))



@app.route('/api/v1/maps/vehicles')
@cross_origin()
def api_vehicles():
    args=dict(request.args)
    args['layer'] = 'vehicles'
    return jsonify(API.get_positions_byargs(system_map,args,system_map.route_descriptions, system_map.collection_descriptions)) # todo 1 fold this into RouteConfig.render_geojson

@app.route('/api/v1/maps/waypoints')
@cross_origin()
def api_waypoints():
    args=dict(request.args)
    args['layer'] = 'waypoints'
    return jsonify(system_map.render_geojson(args))

@app.route('/api/v1/maps/stops')
@cross_origin()
def api_stops():
    args=dict(request.args)
    args['layer'] = 'stops'
    return jsonify(system_map.render_geojson(args))

################################################
# ERROR HANDLER
################################################
@app.errorhandler(404)
def page_not_found(e):
    routereport = Dummy() # setup a dummy routereport for the navbar
    return render_template('error_API_down.html', route_report=routereport), 404


################################################
# CUSTOM FILTERS
################################################

@app.template_filter('strftime_today')
def _jinja2_filter_datetime(timestamp, format='%I:%M %p'):
    return timestamp.strftime(format)

@app.template_filter('strftime_period')
def _jinja2_filter_datetime_by_period(timestamp, period):

    if period == "today":
        format = '%I:%M %p'
    elif period == "yesterday":
        format = '%a %I:%M %p'
    elif period == "weekly":
        format = '%a %I:%M %p'
    elif period == "history":
        format = '%Y-%m-%d %I:%M %p'

    return timestamp.strftime(format)


@app.template_filter('hour_as_int')
def _jinja2_filter_hour_as_int(hour):
    hour = int(hour)
    pretty_time = ''
    if hour == 0:
        pretty_time = ("12 am")
    elif (hour > 0 and hour <10):
        pretty_time = (" {a} am").format(a=hour)
    elif (hour == 10 or hour == 11):
        pretty_time = ("{a} am").format(a=hour)
    elif hour == 12:
        pretty_time = ("12 pm")
    elif (hour > 12 and hour < 24):
        hour = hour -12
        pretty_time = (" {a} pm").format(a=hour)
    elif hour > 23:
        hour = hour - 12
        pretty_time = ("{a} pm").format(a=hour)
    return pretty_time

@app.template_filter('strftime_forever')
def _jinja2_filter_datetime(timestamp, format='%Y-%m-%d %I:%M %p'):
    return timestamp.strftime(format)

@app.template_filter('title')
def _jinja2_filter_titlecase(name):
    return name.title()

@app.template_filter('strftime_timedelta')
def pretty_timedelta(td):
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if days != 0:
        pretty_time = ("{a} days {b} hrs {c} mins").format(a=days, b=hours, c=minutes)
        return pretty_time
    elif hours != 0:
        pretty_time = ("{a} hrs {b} mins").format(a=hours, b=minutes)
        return pretty_time
    else:
        pretty_time = ("{a} mins").format(a=minutes)
    return pretty_time

@app.template_filter('split_')
def splitpart (value, index, char = '_'):
    return value.split(char)[index]

################################################
# MAIN
################################################

if __name__ == "__main__":

    system_map=load_system_map() # n.b. this will be a separate instance
    period_descriptions = system_map.period_descriptions
    route_descriptions = system_map.route_descriptions
    grade_descriptions = system_map.grade_descriptions
    collection_descriptions = system_map.collection_descriptions

    app.run(host='0.0.0.0', debug=True)



