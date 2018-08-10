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
@app.route('/<source>/<route>/<stop>/<period>/arrivals')
def getArrivals(source, route, stop, period):
    arrivals = rc.StopReport(route,stop)
    arrivals.get_arrivals(period)
    return render_template('dev/arrivals.html', arrivals=arrivals)

# 3 simple arrival list with delta
@app.route('/<source>/<route>/<stop>/<period>/delta')
def getDelta(source, route, stop, period):
    arrivals = rc.StopReport(route,stop)
    arrivals.get_arrivals(period)
    delta_list = arrivals.delta_list()
    return render_template('dev/delta.html', delta_list=delta_list)



# PRODUCTION VIEWS


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
