# bus reportcard v1.0
# June 2018

from flask import Flask, render_template
from lib.reportcard_helpers import *

app = Flask(__name__)


@app.route('/<source>/<route>/history')
def getArrivalHistory(source, route):

    history = render_arrivals_history_full(source, route, get_stoplist(route))
    return render_template('arrivals_history_full.html', history=history)


@app.route('/<source>/<route>/<stop>/history')
def getArrivalHistory1Stop(source, route, stop):

    history1stop = render_arrivals_history_1stop(source, route, stop)
    return render_template('arrivals_history_1stop.html', history1stop=history1stop)


@app.route('/<source>/<route>/hourly')
def getHourlyHistory(source, route):

    hourly = render_arrivals_hourly_mean(source, route, get_stoplist(route))
    return render_template('arrivals_history_hourly.html', hourly=hourly)


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)


# this flask app shows the routes
# http://host.org/source/route/function
# e.g. http://bus.host.org:5000/nj/87/history
# e.g. http://bus.host.org:5000/nj/87/hourly

# all it does is make calls to the database. never talks to any of the fetcher functions
# database should be the only point of contact between reportcard-www.py and stopwatcher.py


#######################################################
# TO DO
#######################################################

# HELPERS
#   1. rewrite render_arrivals_* to create json
#   2. write render_arrivals_delays = delays (observed travel time) = compare bus at stop n and stop n+5 using vehicle id and stopid and average across last n vehicles?
#   3. write render_arrivals_adherence = schedule adherence = compared observed arrival time against GTFS schedule using run w/ TransitLand API call?

# TEMPLATES
#   1. sns or matplotlib the JSON into a nice UI

# ARCHIVES / REFACTOR

#   1   think about how to set up processors to rotate / batch yesterdays, last weeks, last months data to static files, and have the routes serve those instead.

