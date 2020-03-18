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

app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}]
)
server = app.server

# Describe the layout/ UI of the app
app.layout = html.Div(
    [dcc.Location(id="url", refresh=False), html.Div(id="page-content")]
)

# todo load this from system_map or collection_descriptions.json or make it a larger bundle of config data like the system_map?
routes = {
    '87 Chicken Sandwich': '87',
    '119 New York': '119'
}



# todo add another callback for the route dropdown, passing the route around
# alt use urlprase or flask to figure out route from url
# e.g. / -> overview or /87 or /speed/87 or /87/speed

# Update page
@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def display_page(pathname):

    if pathname == "/speed":
        return speed.create_layout(app,routes)
    elif pathname == "/frequency":
        return frequency.create_layout(app,routes)
    elif pathname == "/reliability":
        return reliability.create_layout(app,routes)
    elif pathname == "/bunching":
        return bunching.create_layout(app,routes)
    elif pathname == "/news-and-reviews":
        return newsReviews.create_layout(app,routes)
    elif pathname == "/full-view":
        return (
            overview.create_layout(app,routes),
            speed.create_layout(app,routes),
            frequency.create_layout(app,routes),
            reliability.create_layout(app,routes),
            bunching.create_layout(app,routes),
            newsReviews.create_layout(app,routes),
        )
    else:
        return overview.create_layout(app,routes)


# todo build callback to update the active_route display and which data files are loaded
# then build it and the callback https://dash.plot.ly/dash-core-components/dropdown
# https://towardsdatascience.com/dash-a-beginners-guide-d118bd620b5d
# @app.callback(Output('active_route', 'children'), [Input('route_choice', 'value')])
# def output_active_route(route):
#     return u'{}'.format(route)

if __name__ == "__main__":
    app.run_server(debug=True)
