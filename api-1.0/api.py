# based on  https://developersoapbox.com/basic-web-api-using-flask-and-mysql/

from flask import Flask, jsonify
from flaskext.mysql import MySQL

def main():
    app = Flask(__name__)
    mysql = MySQL()

    # MySQL configurations
    app.config['MYSQL_DATABASE_USER'] = 'buswatcher'
    app.config['MYSQL_DATABASE_PASSWORD'] = 'njtransit'
    app.config['MYSQL_DATABASE_DB'] = 'buswatcher'
    app.config['MYSQL_DATABASE_HOST'] = 'localhost'

    mysql.init_app(app)


    @app.route('/')
    def top(rt):
        print ("You cant fetch all the billions of positions, dum dum.")
        return


    # /{n} - returns all the position reports for a given route over all time
    @app.route('/<rt>')
    def routehistory(rt):
        cur = mysql.connect().cursor()
        cur.execute('''select * from buswatcher.positions where rt=rt''')
        r = [dict((cur.description[i][0], value)
                  for i, value in enumerate(row)) for row in cur.fetchall()]
        return jsonify({'myCollection' : r})



    # /daily/{n} - all of the position reports since midnight local time for a given route.
    # /weekly/{n}
    # /monthly/{n}

    # /bus/{n} - returns all the position reports for a specific  vehicle over all time.
    # /bus/daily/{n} - all of the position reports since midnight local time for a given route.
    # /bus/weekly/{n}
    # /bus/monthly/{n}

if __name__ == '__main__':
    app.run()