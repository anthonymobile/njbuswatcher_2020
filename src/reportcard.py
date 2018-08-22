# bus reportcard v0.1
# flask app running on https://host:5000

from flask import Flask, render_template
import lib.ReportCard as rc

from route_config import reportcard_routes

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

#2 route report
@app.route('/<source>/<route>')
def genRouteReport(source, route):
    routereport=rc.RouteReport(source,route,reportcard_routes)
    return render_template('route.html', routereport=routereport)

# # todo write stop view
# 3 stop report

@app.route('/<source>/<route>/<stop>')
def genStopReport(source, route, stop, period='history'):
    arrivals = rc.StopReport(route, stop)
    arrivals.get_arrivals(period)

    return render_template('stop.html', arrivals=arrivals, grade=grade,  route_stop_list=route_stop_list)



################################################
# DEVELOPMENT URLS
################################################

# # 1 list all approaches for a specific source, route, stop, period
# @app.route('/<source>/<route>/<stop>/<period>/approaches')
# def getApproaches(source, route, stop, period):
#     approaches = rc.StopReport(route,stop)
#     approaches.get_approaches(period)
#     return render_template('dev-oldtemplates/approaches.html', approaches=approaches)
#
# # 2 list all arrivals for a specific source, route, stop, period
# @app.route('/<source>/<route>/<stop>/<period>/arrivals')
# def getArrivals(source, route, stop, period):
#     arrivals = rc.StopReport(route,stop)
#     arrivals.get_arrivals(period)
#     route_stop_list=rc.get_stoplist(source,route)
#     map=arrivals.route_map()
#     return render_template('dev-oldtemplates/arrivals.html', arrivals=arrivals, route_stop_list=route_stop_list,map=map)

# custom filters
@app.template_filter('strftime_today')
def _jinja2_filter_datetime(timestamp, format='%I:%M %p'):
    return timestamp.strftime(format)


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)



