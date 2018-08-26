# bus reportcard v0.1
# flask app running on https://host:5000

from flask import Flask, render_template
import lib.ReportCard

from route_config import reportcard_routes,grade_descriptions

import config



app = Flask(__name__)

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
    routereport=lib.ReportCard.RouteReport(source,route,reportcard_routes,grade_descriptions,config.mapbox_access_key)
    return render_template('route_servicepicker.html', routereport=routereport)

#3 route report - with service
@app.route('/<source>/<route>/service/<service>')
def genRouteReport_ServiceStoplist(source, route, service):
    routereport=lib.ReportCard.RouteReport(source,route,reportcard_routes,grade_descriptions,config.mapbox_access_key)
    return render_template('route_servicestoplist.html', routereport=routereport,service=service)


# 4 stop report

@app.route('/<source>/<route>/stop/<stop>')
def genStopReport(source, route, stop, period='history'):
    stopreport = lib.ReportCard.StopReport(route, stop, period)
    routereport = lib.ReportCard.RouteReport(source, route, reportcard_routes, grade_descriptions,
                                             config.mapbox_access_key) # need this stuff to display route-level info on stop page: e.g. routename,grade, etc.
    return render_template('stop.html', stopreport=stopreport, routereport=routereport)


# x standalone route map for debugging

@app.route('/<source>/<route>/mapbox_js')
def mapbox_js(source,route):
    routereport=lib.ReportCard.RouteReport(source,route,reportcard_routes,grade_descriptions,config.mapbox_access_key)
    return render_template(
        'mapbox_js.html', ACCESS_KEY=config.mapbox_access_key, route_data=routereport.route_data
    )


# custom filters
@app.template_filter('strftime_today')
def _jinja2_filter_datetime(timestamp, format='%I:%M %p'):
    return timestamp.strftime(format)


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)



