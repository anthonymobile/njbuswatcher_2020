

# https://pixxel.ml/create-rest-api-with-python-flask-in-5-minutes/


# ALT METHOD::: https://medium.com/python-rest-api-toolkit/build-a-python-rest-api-in-5-minutes-c183c00d3465


from flask import Flask, request
from flask_restful import Resource, Api
from sqlalchemy import create_engine
from json import dumps
from flask.ext.jsonpify import jsonify
from .. import Buses

db_connect = create_engine('sqlite:///chinook.db')
app = Flask(__name__)
api = Api(app)


class Buses(Resource):
    def get(self):
        conn = db_connect.connect()  # connect to database
        query = conn.execute("select * from positions")  # This line performs query and returns json result
        return {'buses': [i[0] for i in query.cursor.fetchall()]}  # Fetches first column that is Employee ID

class Route(Resource):
    def get(self, route_id):
        conn = db_connect.connect()
        query = conn.execute("select * from positions where rt =%d " % int(route_id))
        #??? result = {'data': [dict(zip(tuple(query.keys()), i)) for i in query.cursor]}
        return jsonify(result)


"""

class Tracks(Resource):
    def get(self):
        conn = db_connect.connect()
        query = conn.execute("select trackid, name, composer, unitprice from tracks;")
        result = {'data': [dict(zip(tuple(query.keys()), i)) for i in query.cursor]}
        return jsonify(result)



"""

api.add_resource(Buses, '/buses')  # Route_1
api.add_resource(Routes, '/routes/<route_id>')  # Route_2
# api.add_resource(Routs, '/tracks')  # Route_3


if __name__ == '__main__':
    app.run(port='5002')