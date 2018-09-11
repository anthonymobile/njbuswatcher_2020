
# buswatcher.code4jc.org
# v1.1 API
# implemented with flask_restful and SQLalchemy
# as described at https://impythonist.wordpress.com/2015/07/12/build-an-api-under-30-lines-of-code-with-python-and-flask/
# other docs https://flask-restful.readthedocs.io/en/latest/quickstart.html
# other docs https://flask-restless.readthedocs.io/en/latest/basicusage.html

from flask import Flask, request
from flask_restful import Resource, Api
from sqlalchemy import create_engine
from json import dumps
from datetime import datetime


e = create_engine('mysql+mysqlconnector://buswatcher:njtransit@localhost/bus_position_log')
app = Flask(__name__)
api = Api(app)

# /route/{n} - all of the position reports for a given route LIMIT 50 records

class Routes(Resource):
    def get(self, rt):
        conn = e.connect()
        query = conn.execute("select * from positions where rt='%s' LIMIT 50" % rt)
        #return {'departments': [i[0] for i in query.cursor.fetchall()]} # how to jsonify the results?
        return dumps(query)
api.add_resource(Routes, '/route/<int:rt>')

# Good resource on running these queries using native MYsql
# http://sys-exit.blogspot.com/2013/06/mysql-today-tomorrow-yesterday-this.html

# /route/daily/{n} - all of the position reports since midnight local time for a given route.
class RoutesDaily(Resource):
    def get(self, rt):
        conn = e.connect()
        query = conn.execute("SELECT * FROM table WHERE (rt='%s' AND (timestamp BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 1 day)))" % rt)
        return dumps(query)
api.add_resource(Routes, '/route/daily/<int:rt>')



#
# route for the monthly
class RoutesMonthly(Resource):
    def get(self, year,month,rt):
        # fetch the json and put it into the appropriate container if any and return it)
        return # render_template('index-base.html', message=message) <--- is this right?

#
#
# Static route methods
#
# USING url_for
# https://stackoverflow.com/questions/16351826/link-to-flask-static-files-with-url-for
#
# USING send_from_directory
# https://www.google.com/amp/s/amp.reddit.com/r/learnpython/comments/3g08o6/problem_to_get_a_file_using_send_from_directory/
#
# @app.route('/media/', methods=['GET','POST'])
# def send_foo(filename):
# return send_from_directory('/media/usbhdd1/downloads/', filename, as_attachment=True)
#
# @app.route('/route//', methods=['GET','POST'])
# def fetch_log((logpath+’/%s/%s/%s’+’.json’) % year, month, rt):
# return send_from_directory('/TJ/', filename, as_attachment=False)



api.add_resource(Routes, '/route/monthly/<int:year>/<int:month><int:rt>')



# functions for batch processing

def make_route_monthly(year,month,rt):
    conn = e.connect()
    query = conn.execute("select * from positions where (rt='%s' AND (YEAR(timestamp)=year and MONTH(timestamp)=month)" % rt)
    results=dumps(query)
    path=('/'+str(year)+'/'+str(month)+'/'+'%s.json' % rt)
    return path,results

