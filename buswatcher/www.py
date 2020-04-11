# -*- coding: utf-8 -*-

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

from lib.Layouts import *


# get routes to watch defined in config/collection_descriptions.json
routes_watching = dict()
for k, v in system_map.collection_descriptions.items():
    for r in v['routelist']:
        for rr in system_map.route_descriptions['routedata']:
                if rr['route'] == r:
                    routes_watching[r]=rr['prettyname'] #bug dies here if this isnt defined in route_descrptions.json


#######################################################################################
# APP SETUP + PAGE LAYOUT
#######################################################################################

# init
app = dash.Dash( __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}],external_stylesheets=[dbc.themes.PULSE, '/assets/styles.css'])
server = app.server
app.config['suppress_callback_exceptions'] = True # # suppress callback warnings

# layout scaffold
app.layout = html.Div([dcc.Location(id="url", refresh=False),html.Div(id="page-content")])


# todo redesign callback / url routing
# todo https://dash-bootstrap-components.opensource.faculty.ai/examples/simple-sidebar/#sourceCode
# callback
@app.callback(
        Output("page-content", "children"),
        [Input("url", "pathname")])
def display_page(pathname):

    if pathname is None:
        return 'Loading...'
    elif pathname == '/':
        active_route='87'
        return create_layout(app, routes_watching, active_route)
    else:
        active_route=(pathname[1:])
        return create_layout(app, routes_watching, active_route)



#######################################################################################
# __MAIN__
#######################################################################################
if __name__ == "__main__":
    app.run_server(debug=True)
