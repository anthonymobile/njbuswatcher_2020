# bus reportcard v0.1
# flask app running on https://host:5000
#

from flask import Flask, render_template
import lib.ReportCard as rc

app = Flask(__name__)


# DEVELOPMENT VIEWS

# list all approaches for a specific source, route, stop, period
@app.route('/<source>/<route>/<stop>/<period>')
def getApproaches(source, route, stop, period):
    report = rc.Report.StopReport(source, route)
    return render_template('dev/stop_report.html', stop_report=report.get_approaches(stop,period))

# # same thing, but for every stop on a route
# # list all arrivals (last approach in a contiguous sequence with 'approaching' (method 1) or geolocated bus to stop (method 2)  for a specific source, route,period
# @app.route('/<source>/<route>/<period>')
# def getArrivals(source, route, period):
#     report = ReportCard.RouteReport(source, route, period)
#     return render_template('dev/route_report.html', route_report=report)
#


# REPORT CARD VIEWS
# see OmniGraffle for wireframes
#
# /<source>/<route>/history = entire line all arrivals ever
# /<source>/<route>/weekly  =   "      "  all arrivals this weekdays
# /<source>/<route>/daily   =   "      "  all arrivals today by hour
#
# @app.route('/<source>/<route>/<stop>/<period>')
# def getArrivalHistory1Stop(source, route, stop, period):
#     report = ReportCard.RouteReport(source, route, stop, period)
#     return render_template('route_report.html', route_report=report)


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
