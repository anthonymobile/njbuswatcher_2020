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

# todo load this from system_map or collection_descriptions.json
routes = {
    '87 Journal Square': '87',
    '119 New York': '119'
}


# todo alt solution = use urlprase or flask to
# todo figure out route from url

# todo add another callback for the route dropdown, passing the route around

# Update page
@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def display_page(pathname):

    if pathname == "/speed":
        return speed.create_layout(app,routes)
    elif pathname == "/frequency":
        return frequency.create_layout(app)
    elif pathname == "/reliability":
        return reliability.create_layout(app)
    elif pathname == "/bunching":
        return bunching.create_layout(app)
    elif pathname == "/news-and-reviews":
        return newsReviews.create_layout(app)
    elif pathname == "/full-view":
        return (
            overview.create_layout(app,routes),
            speed.create_layout(app),
            frequency.create_layout(app),
            reliability.create_layout(app),
            bunching.create_layout(app),
            newsReviews.create_layout(app),
        )
    else:
        return overview.create_layout(app,routes)


# todo then build it and the callback https://dash.plot.ly/dash-core-components/dropdown

# https://towardsdatascience.com/dash-a-beginners-guide-d118bd620b5d

# @app.callback(Output('active_route', 'children'), [Input('route_choice', 'value')])
# def output_active_route(route):
#     return u'{}'.format(route)


if __name__ == "__main__":
    app.run_server(debug=True)
