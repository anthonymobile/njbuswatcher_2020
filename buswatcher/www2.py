# bus buswatcher v3.0
# todo rebuild the app a single-page app that updates based on your choices

# mar 2020 - by anthony@starcitygroup.us

# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
from lib.TransitSystem import load_system_map

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(children=[
    html.H1(children='Hello Dash'),

    html.Div(children='''
        Dash: A web application framework for Python.
    '''),

    dcc.Graph(
        id='example-graph',
        figure={
            'data': [
                {'x': [1, 2, 3], 'y': [4, 1, 2], 'type': 'bar', 'name': 'SF'},
                {'x': [1, 2, 3], 'y': [2, 4, 5], 'type': 'bar', 'name': u'Montréal'},
            ],
            'layout': {
                'title': 'Dash Data Visualization'
            }
        }
    )
])

# todo https://dash.plot.ly/urls Multi-Page Apps and URL Support



################################################
# MAIN SCRIPT
################################################

if __name__ == '__main__':
    system_map = load_system_map()
    app.run_server(debug=True)

# if __name__ == "__main__":
#     system_map=load_system_map()
#     app.run(host='0.0.0.0', debug=True)


# after https://medium.com/@trstringer/logging-flask-and-gunicorn-the-manageable-way-2e6f0b8beb2f
if __name__ != "__main__":
    system_map = load_system_map()
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
