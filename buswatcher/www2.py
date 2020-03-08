# bus buswatcher v3.0
# todo rebuild the app a single-page app that updates based on your choices

# mar 2020 - by anthony@starcitygroup.us

import pandas as pd
import pymysql as db
from sqlalchemy import create_engine

# fetch data
def get_arrivals_by_hour(route):

    # database variables
    user = 'buswatcher'
    password = 'njtransit'
    database = 'buses'

    db_connection_str = 'mysql+pymysql://{}:{}@localhost/{}'.format(user, password, database)
    engine = create_engine(db_connection_str)

    conn = connection = engine.connect()

    q = """
        SELECT scheduledstop_log.trip_id, trip_log.trip_id, scheduledstop_log.date, trip_log.rt, \
               scheduledstop_log.run, trip_log.pd, scheduledstop_log.v,  scheduledstop_log.stop_id, \
               scheduledstop_log.stop_name, scheduledstop_log.lat, scheduledstop_log.lon, \
               scheduledstop_log.arrival_timestamp
          FROM scheduledstop_log,trip_log
         WHERE scheduledstop_log.trip_id = trip_log.trip_id
           AND arrival_timestamp is not null 
           AND trip_log.rt = {};
    """.format(route)

    df = pd.read_sql_query(q, conn)
    df['hour_of_arrival_timestamp'] = df['arrival_timestamp'].dt.hour

    return df.groupby(['hour_of_arrival_timestamp']).size().to_frame(name = 'arrivals')


import dash
import dash_core_components as dcc
import dash_html_components as html
from lib.TransitSystem import load_system_map



external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

route=27
df_arrivals_by_hour=get_arrivals_by_hour(route)

app.layout = html.Div(children=[
    html.H1(children='NJBusWatcher'),

    html.Div(children='''
         Residents and businesses depend on NJTransit buses every day. But its hard to evaluate the quality of bus service. That's why we built this site to provide a one-stop shop for bus performance information. Here you can see data on past performance and view maps of current service. 
    '''),


    dcc.Graph(id='arrival-histogram',
              figure={
                'data': [
                    {'x': df_arrivals_by_hour.index, 'y': df_arrivals_by_hour['arrivals'], 'type': 'bar', 'name': 'Arrivals'}
                  ],
                'layout': {
                      'title': 'Arrivals By Hour For A Route'
                  }
              }

    ),

    dcc.Graph(
        id='example-graph',
        figure={
            'data': [
                {'x': [1, 2, 3], 'y': [4, 1, 2], 'type': 'bar', 'name': 'SF'},
                {'x': [1, 2, 3], 'y': [2, 4, 5], 'type': 'bar', 'name': u'Montréal'},
            ],
            'layout': {
                'title': 'Arrivals By Hour For A Route'
            }
        }
    )
]
)
# todo add a callback with a dropdown to pick the route



################################################
# MAIN SCRIPT
################################################

if __name__ == '__main__':
    system_map = load_system_map()
    app.run_server(debug=True)

# if __name__ == "__main__":
#     system_map=load_system_map()
#     app.run(host='0.0.0.0', debug=True)


# # after https://medium.com/@trstringer/logging-flask-and-gunicorn-the-manageable-way-2e6f0b8beb2f
# if __name__ != "__main__":
#     system_map = load_system_map()
#     gunicorn_logger = logging.getLogger("gunicorn.error")
#     app.logger.handlers = gunicorn_logger.handlers
#     app.logger.setLevel(gunicorn_logger.level)
