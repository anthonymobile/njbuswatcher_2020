# bus reportcard v0.1
# flask app running on https://host:5000
#

from flask import Flask, render_template
import lib.ReportCard

app = Flask(__name__)


# DEVELOPMENT VIEWS

# list all arrivals for a specific source, route, stop, period
@app.route('/<source>/<route>/<stop>/<period>')
def getArrivals(source, route, stop, period):
    report = ReportCard.StopReport(source, route)
    return render_template('stop_report.html', stop_report=report.show_arrivals(period,stop))

# same thing, but for every stop on a route
# list all arrivals for a specific source, route,period
@app.route('/<source>/<route>/<period>')
def getArrivals(source, route, period):
    report = ReportCard.RouteReport(source, route, period)
    return render_template('route_report.html', route_report=report)



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
