
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

def main():

    e = create_engine('mysql+mysqlconnector://buswatcher:njtransit@localhost/bus_position_log')
    app = Flask(__name__)
    api = Api(app)

    class Routes(Resource):
        def get(self, route_no):
            conn = e.connect()
            query = conn.execute("select * from positions where rt='%s' from positions" % route_no)
            return {'departments': [i[0] for i in query.cursor.fetchall()]} # how to jsonify the results?

    api.add_resource(Routes, '/route/<string:rt>')

    '''
    class Departmental_Salary(Resource):
        def get(self, department_name):
            conn = e.connect()
            query = conn.execute("select * from salaries where Department='%s'" % department_name.upper())
            # Query the result and get cursor.Dumping that data to a JSON is looked by extension
            result = {'data': [dict(zip(tuple(query.keys()), i)) for i in query.cursor]}
            return result
            # We can have PUT,DELETE,POST here. But in our API GET implementation is sufficient
   
    api.add_resource(Departments_Meta, '/departments')
    '''

if __name__ == '__main__':
    app.run()