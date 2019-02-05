# database setting
conn_str = 'sqlite:///jc_buswatcher.db'

# bus reportcard v2.0
# january 2019 - by anthony@bitsandatoms.net

################################################
# IMPORTS
################################################
import datetime, logging, sys

from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
from flask import jsonify, make_response, send_from_directory
from flask_cors import CORS, cross_origin

import lib.BusAPI as BusAPI
import lib.API as API
import lib.wwwAPI as wwwAPI
from lib.DataBases import DBConfig, SQLAlchemyDBConnection, Trip, BusPosition, ScheduledStop


# import lib.DataBases as db

# import lib.WebAPI as WebAPI

################################################
# APP
################################################
app = Flask(__name__, static_url_path='/static')
CORS(app, support_credentials=True)
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
# APPLICATION DATA IMPORT
################################################
from route_config import reportcard_routes,grade_descriptions

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


#3 home page
@app.route('/')
def displayHome():
    # routereport = routereport # setup a dummy for the navbar
    class Dummy():
        def __init__(self):
            self.routename = 'NJTransit'
    routereport = Dummy()

    citywide_waypoints_geojson, citywide_stops_geojson = wwwAPI.citymap_geojson(reportcard_routes)

    return render_template('index.html', citywide_waypoints_geojson=citywide_waypoints_geojson, citywide_stops_geojson=citywide_stops_geojson,routereport=routereport,reportcard_routes=reportcard_routes)


#4 route report
@app.route('/<source>/<route>')
@cache.cached(timeout=3600) # cache for 1 hour
def genRouteReport(source, route):

    # routereport = ReportCard.RouteReport(source, route, reportcard_routes, grade_descriptions)

    # routereport = routereport # setup a dummy for the navbar
    class Dummy():
        def __init__(self):
            self.routename = 'NJTransit'
    routereport = Dummy()

    # period='weekly'
    # bunchingreport, grade_letter, grade_numeric, grade_description, time_created = routereport.load_bunching_leaderboard( route)
    # return render_template('route.html', routereport=routereport, bunchingreport=bunchingreport, period=period, grade_letter=grade_letter, grade_numeric=grade_numeric, grade_description=grade_description, time_created=time_created)

    return render_template('route.html',routereport=routereport, source=source, route=route)

           # #5 stop report
# @app.route('/<source>/<route>/stop/<stop>/<period>')
# @cache.cached(timeout=60) # cache for 1 minute
# def genStopReport(source, route, stop, period):
#     stopreport = ReportCard.StopReport(route, stop, period)
#     hourly_frequency = stopreport.get_hourly_frequency(route, stop, period)
#     routereport = ReportCard.RouteReport(source, route, reportcard_routes, grade_descriptions)
#     predictions = BusAPI.parse_xml_getStopPredictions(BusAPI.get_xml_data('nj', 'stop_predictions', stop=stop, route='all'))
#
#     return render_template('stop.html', stopreport=stopreport, hourly_frequency=hourly_frequency, routereport=routereport, predictions=predictions,period=period)


################################################
# API
################################################

# /api/v1/positions?rt=87&period={ow, daily,yesterday,history}
@app.route('/api/v1/positions')
@cross_origin()
def api_positions_route():
    args=request.args
    return jsonify(API.get_positions_byargs(args))

# # ARRIVALS ARGS-BASED
# # /api/v1/arrivals?rt=87&period={daily,yesterday,weekly,history} -- historical from stop_approaches_log database
# @app.route('/api/v1/arrivals')
# @cross_origin()
# def api_arrivals_route():
#     args=request.args
#     arrivals_log_df = WebAPI.get_arrivals_byargs(args)
#     arrivals_log_json = make_response(arrivals_log_df.to_json(orient="records"))
#     return arrivals_log_json


################################################
# TRIPWATCHER DIAGNOSTIC DASHBOARD
################################################

# run dash
@app.route('/<source>/<route>/dash')
def displayApproachDash(source,route):

    with SQLAlchemyDBConnection(DBConfig.conn_str) as db:

        todays_date = datetime.datetime.today().strftime('%Y%m%d')
        # grab list of vehicle and run numbers on the road now
        v_list=[]
        run_list=[]
        v_route = BusAPI.parse_xml_getBusesForRoute(BusAPI.get_xml_data(source, 'buses_for_route', route=route))
        for v in v_route:
            v_list.append(v.id)
            run_list.append(v.run)
        buses_dash=dict()
        for b in v_list:
            v_as_list = []
            v_as_list.append(b)
            buses_dash[b]=db.session.query(BusPosition) \
            .filter(BusPosition.id.in_(v_as_list)) \
            .filter(BusPosition.run.in_(run_list)) \
            .order_by(BusPosition.timestamp.desc()) \
            .order_by(BusPosition.stop_id.desc())
        # for b in v_list:
        #     v_as_list = []
        #     v_as_list.append(b)
        #     buses_dash[b]=db.session.query(BusPosition) \
        #     .filter(BusPosition.id.in_(v_as_list)) \
        #     .filter(BusPosition.run.in_(run_list)) \
        #     .order_by(BusPosition.timestamp.desc()) \
        #     .order_by(BusPosition.stop_id.desc()) \
        #     .limit(20)

    return render_template('approach_dash.html', busdash=buses_dash, route=route)

# trip dash
@app.route('/<source>/<route>/dash/<run>')
def displayTripDash(source,route,run):

    with SQLAlchemyDBConnection(DBConfig.conn_str) as db:

        # compute trip_ids
        todays_date = datetime.datetime.today().strftime('%Y%m%d')
        trip_id_list=[]
        v_on_route = BusAPI.parse_xml_getBusesForRoute(BusAPI.get_xml_data(source, 'buses_for_route', route=route))
        for v in v_on_route:
            if v.run == run:
                trip_id = (('{a}_{b}_{c}').format(a=v.id, b=v.run, c=todays_date))
            else:
                pass
        trips_dash = dict()
        # load the trip card
        scheduled_stops = db.session.query(ScheduledStop) \
            .join(Trip) \
            .filter(Trip.trip_id == trip_id) \
            .order_by(ScheduledStop.pkey.asc()) \
            .all()
        trips_dash[trip_id]=scheduled_stops

    return render_template('trip_dash.html', tripdash=trips_dash, route=route)





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

################################################
# MAIN
################################################

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)



