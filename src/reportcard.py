# bus reportcard v0.1
# flask app running on https://host:5000
#

from flask import Flask, render_template
import lib.ReportCard as rc

app = Flask(__name__)


# DEVELOPMENT VIEWS

# 1 list all approaches for a specific source, route, stop, period
@app.route('/<source>/<route>/<stop>/<period>/approaches')
def getApproaches(source, route, stop, period):
    approaches = rc.StopReport(route,stop)
    approaches.get_approaches(period)
    return render_template('dev/approaches.html', approaches=approaches)

# 2 list all arrivals for a specific source, route, stop, period
# method 1: last approach in a contiguous sequence with 'approaching'
@app.route('/<source>/<route>/<stop>/<period>/arrivals')
def getArrivals1(source, route, stop, period):
    arrivals1 = rc.StopReport(route,stop)
    arrivals1.get_arrivals1(period)
    return render_template('dev/arrivals.html', arrivals=arrivals1)

# method 2: geolocated bus to stop using route log tables (e.g. routelog_87) and stop lat/lon from Route.Stop class
@app.route('/<source>/<route>/<stop>/<period>/arrivals')
def getArrivals2(source, route, stop, period):
    arrivals2 = rc.StopReport(route,stop)
    arrivals2.get_arrivals2(period)
    return render_template('dev/arrivals.html', arrivals=arrivals2)





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
