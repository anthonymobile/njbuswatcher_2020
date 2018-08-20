# bus reportcard v0.1
# flask app running on https://host:5000

from flask import Flask, render_template
import lib.ReportCard as rc
from util import assets

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
#    return app.send_static_file('/index.html')
    return render_template('index.html')


# 2 reportcard - for a route
@app.route('/<source>/<route>/<stop>')
def genReportCard(source, route, stop, period='daily'):

    arrivals = rc.StopReport(route, stop)
    arrivals.get_arrivals(period)

    grade=rc.RouteGrade(route)
    grade.compute_grade()

    route_stop_list = rc.get_stoplist(source, route)

    # map = arrivals.route_map() # doesnt work, wont... need to replace
    # bunching_report = TK
    # reliability_report = TK

    # return render_template('route.html', arrivals=arrivals, route_stop_list=route_stop_list, map=map, bunching_report=bunching_report, reliability_report=reliability_report)

    return render_template('route.html', arrivals=arrivals, grade=grade,  route_stop_list=route_stop_list)


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
@app.template_filter('strftime_custom')
def _jinja2_filter_datetime(timestamp, format='%a %b %d %I:%M %p'):
    return timestamp.strftime(format)


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)



