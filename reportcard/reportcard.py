# bus reportcard v2.0
# february 2019 - by anthony@bitsandatoms.net

################################################
# VIP INSTANCE CONFIG
################################################

class Dummy():
    def __init__(self):
        self.routename = 'Jersey City'

################################################
# IMPORTS
################################################
import datetime, logging, sys
import geojson, json

from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
from flask import jsonify, make_response, send_from_directory
from flask_cors import CORS, cross_origin

import lib.BusAPI as BusAPI
import lib.API as API
import lib.wwwAPI as wwwAPI
from lib.DataBases import SQLAlchemyDBConnection, Trip, BusPosition, ScheduledStop

################################################
# ROUTE + APP CONFIG
################################################
from route_config import reportcard_routes, grade_descriptions

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
# URLS
################################################

#-------------------------------------------------------------Index
@app.route('/')
def displayHome():
    routereport = Dummy() # setup a dummy routereport for the navbar
    return render_template('index.html', reportcard_routes=reportcard_routes, routereport=routereport)


#-------------------------------------------------------------Route
@app.route('/<source>/<route>/<period>')
def genRouteReport(source, route, period):
    route_report = wwwAPI.RouteReport(source, route, period)

    return render_template('route.html', source=source, route=route, period=period, routereport=route_report)

#------------------------------------------------------------Stop
# /<source>/<route>/stop/<stop>/<period>
@app.route('/<source>/<route>/stop/<stop>/<period>')
#@cache.cached(timeout=60) # cache for 1 minute
def genStopReport(source, route, stop, period):
    stop_report = wwwAPI.StopReport(source, route, stop, period)
    route_report = wwwAPI.RouteReport(source, route, period)
    predictions = BusAPI.parse_xml_getStopPredictions(BusAPI.get_xml_data('nj', 'stop_predictions', stop=stop, route='all'))

    return render_template('stop.html', source=source, stop=stop, period=period, stopreport=stop_report, reportcard_routes=reportcard_routes,predictions=predictions, routereport=route_report)

#-------------------------------------------------------------FAQ
@app.route('/faq')
def displayFAQ():
    routereport = Dummy() #  setup a dummy routereport for the navbar
    return render_template('faq.html', reportcard_routes=reportcard_routes, routereport=routereport)

#-------------------------------------------------------------API docs
@app.route('/api')
def displayAPI():
    routereport = Dummy() #  setup a dummy routereport for the navbar
    return render_template('api.html', reportcard_routes=reportcard_routes, routereport=routereport)


################################################
# API
################################################

# map layer geojson generator
#
# /api/v1/maps?
#
#   layer=waypoints&rt=87               waypoints for single route
#   layer=waypoints&rt=all              waypoints for ALL routes
#   layer=stops&rt=87                   stops for single route
#   layer=stops&rt=87&stop_id=30189     stop for single stop
#   layer=vehicles&rt=87               vehicles for single stop
#   layer=vehicles&rt=all              vehicles forALL routes
#

@app.route('/api/v1/maps')
@cross_origin()
def api_map_layer():
    args=request.args

    if args['layer'] == 'vehicles':
        return jsonify(API.get_positions_byargs(args, reportcard_routes))
    else:
        return jsonify(API.get_map_layers(args, reportcard_routes))



################################################
# ERROR HANDLER
################################################
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error_API_down.html'), 404


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



