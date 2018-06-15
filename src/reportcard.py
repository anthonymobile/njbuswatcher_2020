# bus reportcard
# flask app running on https://host:5000
#
# shows a report_card
#
# v0.1 single stop routes
# /<source>/<route>/<stop>/history = single stop all arrivals ever
# /<source>/<route>/<stop>/daily   =   "      "  all arrivals since midnight
# /<source>/<route>/<stop>/now     =   "      "  all arrivals last 120 minutes

# INTEGRATION NOTES
# all it does is make calls to the helper functions
# to read from web API and write to local database
# database should be the only point of contact
# between reportcard.py and stopwatcher.py


from flask import Flask, render_template

app = Flask(__name__)

@app.route('/<source>/<route>/<stop>/history')
def getArrivalHistory1Stop(source, route, stop):

    history1stop = render_arrivals_history_1stop(source, route, stop)
    return render_template('arrivals_history_1stop.html', history1stop=history1stop)

# WIP - Need to write helper function: render_arrivals_daily_1stop
# @app.route('/<source>/<route>/<stop>/daily')
# def getArrivalDaily1Stop(source, route, stop):
#
#     history1stop = render_arrivals_daily_1stop(source, route, stop)
#     return render_template('arrivals_daily_1stop.html', daily1stop=daily1stop)
#
# WIP - Need to write helper function: render_arrivals_now_1stop
# @app.route('/<source>/<route>/<stop>/now')
# def getArrivalNow1Stop(source, route, stop):
#
#     history1stop = render_arrivals_now_1stop(source, route, stop)
#     return render_template('arrivals_now_1stop.html', now1stop=now1stop)



# -----------------------------------------------------------------------------
# FOR FUTURE USE
# @app.route('/<source>/<route>/history')
# def getArrivalHistory(source, route):
#
#     history = render_arrivals_history_full(source, route, get_stoplist(route))
#     return render_template('arrivals_history_full.html', history=history)

# FOR FUTURE USE
# @app.route('/<source>/<route>/hourly')
# def getHourlyHistory(source, route):
#
#     hourly = render_arrivals_hourly_mean(source, route, get_stoplist(route))
#     return render_template('arrivals_history_hourly.html', hourly=hourly)
# -----------------------------------------------------------------------------


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
