# busreport.code4jc.org

import sqlite3, argparse

parser = argparse.ArgumentParser()
mysql_parser.add_argument('--route', dest='route', required=True, help='Route for report card display')
args = parser.parse_args()

# grab only the rows of arriving buses into a data frame, sorted by stop and time
conn = sqlite3.connect('data/%s.db' % args.route)
arrival_query = ('SELECT * FROM stop_predictions WHERE (rd = %s AND pt = "Approaching") ORDER BY stop_id,timestamp;' % args.route)
df = pd.read_sql_query(arrival_query, conn)
print df

#
# ------------------------------------------------------------ PROGRESS ----------------------
#

# 1. Frequency of service analysis. This is simply calculated by looking at how often a bus on a particular route passes a given stop.
# this route does it for all stops on the route, later should do it for specified stops
# create list of only observations of buses arriving at stops
# calculate the mean time between arrivals for various periods (last hour, last day, last week, rush hour only, etc)
# for stop in stop_id:    # not sure if this is how to do it, do i need to unique(stop_id) or something)
    # for a given stop
    # find all the buses in the desired time window
    # sort the buses by timestamp
    # calculate the time in minutes between them
    # average over the # of buses
# q: what happens when there are gaps in the data? can detect this?


2. Travel time analysis. How long is it taking to get from one stop to the next. We can do this by tracking individual vehicles and seeing how long it takes them to get from one stop to the next.
# is there a unique run id? for each date, calculate travel time on each segment of the route and display average for all buses?
#
#

# 3. render the page

# first in text, later in graphics

# 4. render the route

app = Flask(__name__)
api = Api(app)
@app.route('/<path:path>')
def staticHost(self, path):
    try:
        return flask.send_from_directory(app.config['RESULT_STATIC_PATH'], path)
    except werkzeug.exceptions.NotFound as e:
        if path.endswith("/"):
            return flask.send_from_directory(app.config['RESULT_STATIC_PATH'], path + "index.html")
        raise e
