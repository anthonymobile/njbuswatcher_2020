# todo 1 merge statewide branch back into new_localizer

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
from dateutil import parser
from datetime import datetime, timedelta

from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
from flask import jsonify
from flask_cors import CORS, cross_origin

import buswatcher.lib.API as API
import buswatcher.lib.BusAPI as BusAPI
import buswatcher.lib.RouteConfig as RouteConfig
import buswatcher.lib.wwwAPI as wwwAPI


################################################
# ROUTE + APP CONFIG
################################################
from buswatcher.lib.RouteConfig import load_config
route_definitions, grade_descriptions, collection_descriptions = load_config()

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

def load_collection_routes(collection_url):
# get list of routes in collection from route_config
    d1, d2, collection_descriptions = load_config()
    collection_metadata=dict()
    for collection in collection_descriptions:
        if collection['collection_url'] == collection_url:
            collection_metadata = collection
            break
        else:
            continue
    return collection_metadata


def maintenance_check(f):
    def wrapper(*args,**kwargs):
        now = datetime.now()
        # check and update route definitions
        print (route_definitions['last_updated'])
        try:
            route_definitions_last_updated = parser.parse(route_definitions['last_updated'])
        except:
            route_definitions_last_updated = parser.parse('2000-01-01 01:01:01')
        route_definitions_ttl = timedelta(seconds=route_definitions['ttl'])
        if route_definitions_last_updated + route_definitions_ttl > now:
            RouteConfig.fetch_update_route_metadata()
        # todo 2 other nightly/hourly tasks
        # for r in route_definitions['route_definitons']:
        #     # create base RouteReport instance
        #     routereport = wwwAPI.RouteReport(source, rt_no['route'])
        #     # generate individual reports to a pickle file
        #     # generate bunching leaderboard
        #     routereport.generate_bunching_leaderboard(route=rt_no['route'], period=period)
        #     # generate other reports
        #     # e.g. routereport.get_bunching_leaderboard()

        return f(*args,**kwargs)
    return wrapper



################################################
# URLS
################################################

#-------------------------------------------------------------Statewide Index
@app.route('/')
@maintenance_check(route_definitions=route_definitions)
def displayIndex():
    d1, d2, collection_descriptions = load_config()
    routereport = Dummy() # setup a dummy routereport for the navbar
    return render_template('index.jinja2', collection_descriptions=collection_descriptions, route_definitions=route_definitions, routereport=routereport)


#-------------------------------------------------------------City Index
@app.route('/<collection_url>')
def displayCollection(collection_url):
    collection_metadata=load_collection_routes(collection_url)
    routereport = Dummy()  # setup a dummy routereport for the navbar
    return render_template('collection.jinja2',collection_metadata=collection_metadata, route_definitions=route_definitions, routereport=routereport)


#-------------------------------------------------------------Route

@app.route('/<collection_url>/<route>/<period>')
def genRouteReport(collection_url,route, period):
    source=source_global
    collection_metadata=load_collection_routes(collection_url)
    route_report = wwwAPI.RouteReport(source, route, period)
    return render_template('route.jinja2', collection_metadata=collection_metadata, route=route, period=period, routereport=route_report)

#------------------------------------------------------------Stop
# /<source>/<route>/stop/<stop>/<period>
@app.route('/<collection_url>/<route>/stop/<stop>/<period>')
#@cache.cached(timeout=60) # cache for 1 minute
def genStopReport(collection_url, route, stop, period):
    source = source_global
    collection_metadata=load_collection_routes(collection_url)
    stop_report = wwwAPI.StopReport(source, route, stop, period)
    route_report = wwwAPI.RouteReport(source, route, period)
    predictions = BusAPI.parse_xml_getStopPredictions(BusAPI.get_xml_data('nj', 'stop_predictions', stop=stop, route='all'))

    return render_template('stop.jinja2', collection_metadata=collection_metadata, source=source, stop=stop, period=period, stopreport=stop_report, reportcard_routes=route_definitions,predictions=predictions, routereport=route_report)

#-------------------------------------------------------------FAQ
@app.route('/faq')
def displayFAQ():
    routereport = Dummy() #  setup a dummy routereport for the navbar
    return render_template('faq.jinja2', route_definitions=route_definitions, routereport=routereport)

#-------------------------------------------------------------API docs
@app.route('/api')
def displayAPI():
    routereport = Dummy() #  setup a dummy routereport for the navbar
    return render_template('api.jinja2', reportcard_routes=route_definitions, routereport=routereport)


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



@app.route('/api/v1/maps')
@cross_origin()
def api_map_layer():
    args=request.args

    if args['layer'] == 'vehicles':
        return jsonify(API.get_positions_byargs(args,route_definitions,collection_descriptions))
    else:
        return jsonify(API.get_map_layers(args,route_definitions,collection_descriptions))



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
    if period == "daily":
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
    app.run(host='0.0.0.0', debug=True)



