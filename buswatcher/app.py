# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from pages import (
    overview,
    speed,
    frequency,
    reliability,
    bunching,
    newsReviews,
)

# get system map
from lib.TransitSystem import load_system_map
system_map=load_system_map()

app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}]
)
server = app.server

# Describe the layout/ UI of the app
app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        html.Div(id="page-content"),
        html.Div(id='active-route', style={'display': 'none'})
    ]
)

# suppress callback warnings
app.config['suppress_callback_exceptions'] = True

# get routes defined in config/collection_descriptions.json
routes = dict()
for k, v in system_map.collection_descriptions.items():
    for r in v['routelist']:
        for rr in system_map.route_descriptions['routedata']:
                if rr['route'] == r:
                    routes[r]=rr['prettyname'] #bug dies here if this isnt defined in route_desrptions.json

#     active_route = '{"active_route":"87"}'

# Update page
@app.callback(
        Output("page-content", "children"),
        [Input("url", "pathname"),
         Input("active-route","children")])
def display_page(pathname,active_route):

    if pathname == "/speed":
        return speed.create_layout(app,routes) #todo add (app,routes,active_route) and so on
    elif pathname == "/frequency":
        return frequency.create_layout(app,routes) #todo add (app,routes,active_route) and so on
    elif pathname == "/reliability":
        return reliability.create_layout(app,routes) #todo add (app,routes,active_route) and so on
    elif pathname == "/bunching":
        return bunching.create_layout(app,routes) #todo add (app,routes,active_route) and so on
    elif pathname == "/news-and-reviews":
        return newsReviews.create_layout(app,routes) #todo add (app,routes,active_route) and so on
    elif pathname == "/full-view":
        return (
            overview.create_layout(app,routes,active_route), #todo add (app,routes,active_route) and so on
            speed.create_layout(app,routes), #todo add (app,routes,active_route) and so on
            frequency.create_layout(app,routes), #todo add (app,routes,active_route) and so on
            reliability.create_layout(app,routes), #todo add (app,routes,active_route) and so on
            bunching.create_layout(app,routes), #todo add (app,routes,active_route) and so on
            newsReviews.create_layout(app,routes), #todo add (app,routes,active_route) and so on
        )
    else:

        return overview.create_layout(app,routes,active_route)



# pass the chosen route back
# https://dash.plotly.com/sharing-data-between-callbacks
#  https://stackoverflow.com/questions/56762733/flask-dash-passing-a-variable-generated-in-a-callback-to-another-callback
@app.callback(Output('active_route', 'children'), [Input('route_choice', 'value')])
def output_active_route(route):
    active_route_json = "{'active_route':{}}".format(route)

    return active_route_json

if __name__ == "__main__":
    app.run_server(debug=True)
