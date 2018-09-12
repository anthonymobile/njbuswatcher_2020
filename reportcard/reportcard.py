# bus reportcard v0.1
# flask app running on https://host:5000

from flask import Flask, render_template
import lib.ReportCard
import lib.BusAPI

app = Flask(__name__)
app.config.from_pyfile('config.py')
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
# PRODUCTION URLS
################################################

#1 home page
@app.route('/')
def displayHome():
    return render_template('index.html', reportcard_routes=reportcard_routes)

#2 route report - choose service
@app.route('/<source>/<route>')
def genRouteReport_ServicePicker(source, route):
    routereport=lib.ReportCard.RouteReport(source,route,reportcard_routes,grade_descriptions)
    return render_template('route_servicepicker.html', routereport=routereport)

#3 route report - with service
@app.route('/<source>/<route>/service/<service>')
def genRouteReport_ServiceStoplist(source, route, service):
    routereport=lib.ReportCard.RouteReport(source,route,reportcard_routes,grade_descriptions)
    return render_template('route_servicestoplist.html', routereport=routereport,service=service)

# 4 stop report
@app.route('/<source>/<route>/stop/<stop>')
def genStopReport(source, route, stop, period='daily'):
    stopreport = lib.ReportCard.StopReport(route, stop, period)
    routereport = lib.ReportCard.RouteReport(source, route, reportcard_routes, grade_descriptions)
    predictions = lib.BusAPI.parse_xml_getStopPredictions(lib.BusAPI.get_xml_data('nj', 'stop_predictions', stop=stop, route='all'))
    return render_template('stop.html', stopreport=stopreport, routereport=routereport, predictions=predictions)


# custom filters
@app.template_filter('strftime_today')
def _jinja2_filter_datetime(timestamp, format='%I:%M %p'):
    return timestamp.strftime(format)

@app.template_filter('strftime_forever')
def _jinja2_filter_datetime(timestamp, format='%Y-%m-%d %I:%M %p'):
    return timestamp.strftime(format)

@app.template_filter('strftime_timedelta')
def pretty_timedelta(td):
    days, hours, minutes = td.days, td.seconds // 3600, td.seconds // 60 % 60
    if days is True:
        pretty_time = ("%s days %s hours %s mins") % days, hours, minutes
    elif hours is True:
        pretty_time = ("%s hours %s mins") % hours, minutes
    else:
        pretty_time = ("%s mins") % minutes
    return pretty_time


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)



