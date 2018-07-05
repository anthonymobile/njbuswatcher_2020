# bus reportcard
# flask app running on https://host:5000
#
#
# v0.1 single stop routes
# stats are aggregated for


from flask import Flask, render_template

app = Flask(__name__)

# ROUTE VIEW
# /<source>/<route>/history = single stop all arrivals ever
# /<source>/<route>/daily   =   "      "  all arrivals since midnight
# /<source>/<route>/now     =   "      "  all arrivals last 120 minutes

@app.route('/<source>/<route>/<stop>/<period>')
def getArrivalHistory1Stop(source, route, stop, period):

    from ReportCard import *
    report = ReportCard(source, route, stop, period)
    return render_template('route_report.html', route_report=report)

# STOP VIEW
# /<source>/<route>/<stop>/history = single stop all arrivals ever
# /<source>/<route>/<stop>/daily   =   "      "  all arrivals since midnight
# /<source>/<route>/<stop>/now     =   "      "  all arrivals last 120 minutes

@app.route('/<source>/<route>/<stop>/<period>')
def getArrivalHistory1Stop(source, route, stop, period):

    from ReportCard import *
    report = ReportCard(source, route, stop, period)
    return render_template('stop_report.html', stop_report=report)


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
