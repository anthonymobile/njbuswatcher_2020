# -*- coding: utf-8 -*-
import json
import pathlib

# dash libraries
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Input, Output

# buswatcher libraries
from lib.TransitSystem import load_system_map
import lib.Reports as reports
import lib.Maps as maps

# get relative data folder
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("../data").resolve()

### GET buswatcher CONFIG

# get system map
system_map=load_system_map()

# get routes to watch defined in config/collection_descriptions.json
routes = dict()
for k, v in system_map.collection_descriptions.items():
    for r in v['routelist']:
        for rr in system_map.route_descriptions['routedata']:
                if rr['route'] == r:
                    routes[r]=rr['prettyname'] #bug dies here if this isnt defined in route_descrptions.json

### INITIALIZE dash app
app = dash.Dash( __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}])
server = app.server
app.config['suppress_callback_exceptions'] = True # # suppress callback warnings

# Describe the layout/ UI of the app
app.layout = html.Div(
                        [
                            dcc.Location(id="url", refresh=False),
                            html.Div(id="page-content")
                        ]
                      )



# todo replace dropdown with a list of linked route #s each links to the URL /87 and active_route is populated by reading the URL
# Update page
@app.callback(
        Output("page-content", "children"),
        [Input("url", "pathname")])
def display_page(pathname):
    try:
        active_route = int(pathname)
    except ValueError:
        active_route = '87'

    return create_layout(app, routes, active_route)

# # different approach
# @app.callback(
#     Output("page-content", "children"),
#     [Input("route_choice", "value")])
#
# def display_page(route_choice):
#
#     return create_layout(app, routes, route_choice)


def create_layout(app, routes, active_route):

    # print('create_layout thinks active_route is {}'.format(active_route)) #debugging

    # load data
    # todo plug in live data source by making a call to wwwAPI here e.g. df_route_summary = wwwAPI.get_route_summary(route) where route is a callback from a dropdown
    _df_route_summary = reports.get_route_summary(active_route)

    # Page layouts
    return html.Div(
        [
            Header(app, routes, active_route),
            # page 1
            html.Div(
                [
                    # Row 1
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.H5(id="active_route"), #bug this is the hidden callback
                                    html.H5("How Is the {} Doing?".format(active_route)), #bug active_route is not getting updated here, because it was passed in?
                                    html.H6("Journal Square — Hoboken"),
                                    html.Br([]),
                                    html.P(
                                        "\
                                        Residents and businesses depend on NJTransit buses every day. But its hard to\
                                        evaluate the quality of bus service.\
                                        That's why we built this site to provide a one-stop shop for bus performance\
                                        information. Here you can see data on past performance and view maps of current\
                                        service.",
                                        style={"color": "#ffffff"},
                                        className="row",
                                    ),
                                    get_route_menu(routes, active_route),


                                ],
                                className="product",
                            ),

                        ],
                        className="row",
                    ),
                    # Row 2
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.H6(
                                        ["Route Overview"], className="subtitle padded"
                                    ),
                                    html.Table(make_dash_table(_df_route_summary)),
                                    html.Br([]),
                                ],
                                className="six columns",
                            ),

                            html.Div(
                                [
                                    html.H6(
                                        "Route Map",
                                        className="subtitle padded",
                                    ),

                                    dcc.Graph(id="map", config={"responsive": True},
                                              figure=maps.gen_map(active_route)
                                              ),
                                    html.Br([]),

                                ],

                                className="six columns",
                            ),





                        ],
                        className="row ",
                    ),

                    # Row 3 NEW
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.H6(
                                        "Frequency",
                                        className="subtitle padded",
                                    ),
                                    dcc.Graph(
                                        id="graph-2",
                                        figure={
                                            "data": make_dash_chart_bar(reports.get_frequency(active_route)),

                                            "layout": go.Layout(
                                                autosize=True,
                                                title="",
                                                font={"family": "Raleway", "size": 10},
                                                height=200,
                                                width=340,
                                                hovermode="closest",
                                                margin={
                                                    "r": 20,
                                                    "t": 20,
                                                    "b": 40,
                                                    "l": 50,
                                                },
                                                showlegend=False,
                                                xaxis={
                                                    "autorange": True,
                                                    "linecolor": "rgb(0, 0, 0)",
                                                    "linewidth": 1,
                                                    "range": [6, 16],
                                                    "showgrid": False,
                                                    "showline": True,
                                                    "title": "hour of day",
                                                    "type": "linear",
                                                },
                                                yaxis={
                                                    "autorange": False,
                                                    "gridcolor": "rgba(127, 127, 127, 0.2)",
                                                    "mirror": False,
                                                    "nticks": 4,
                                                    "range": [0, 60],
                                                    "showgrid": True,
                                                    "showline": True,
                                                    "ticklen": 10,
                                                    "ticks": "outside",
                                                    "title": "minutes",
                                                    "type": "linear",
                                                    "zeroline": False,
                                                    "zerolinewidth": 4,
                                                },
                                            ),
                                        },
                                        config={"displayModeBar": False},
                                    ),
                                ],
                                className="six columns",
                            ),

                            html.Div(
                                [

                                    html.H6(
                                        "Reliability",
                                        className="subtitle padded",
                                    ),
                                    dcc.Graph(
                                        id="graph-2",
                                        figure={
                                            "data": make_dash_chart_bar(reports.get_reliability(active_route)),

                                            "layout": go.Layout(
                                                autosize=True,
                                                title="",
                                                font={"family": "Raleway", "size": 10},
                                                height=200,
                                                width=340,
                                                hovermode="closest",
                                                margin={
                                                    "r": 20,
                                                    "t": 20,
                                                    "b": 40,
                                                    "l": 50,
                                                },
                                                showlegend=False,
                                                xaxis={
                                                    "autorange": True,
                                                    "linecolor": "rgb(0, 0, 0)",
                                                    "linewidth": 1,
                                                    "range": [6, 16],
                                                    "showgrid": False,
                                                    "showline": True,
                                                    "title": "hour of day",
                                                    "type": "linear",
                                                },
                                                yaxis={
                                                    "autorange": False,
                                                    "gridcolor": "rgba(127, 127, 127, 0.2)",
                                                    "mirror": False,
                                                    "nticks": 4,
                                                    "range": [0, 60],
                                                    "showgrid": True,
                                                    "showline": True,
                                                    "ticklen": 10,
                                                    "ticks": "outside",
                                                    "title": "minutes",
                                                    "type": "linear",
                                                    "zeroline": False,
                                                    "zerolinewidth": 4,
                                                },
                                            ),
                                        },
                                        config={"displayModeBar": False},
                                    ),
                                ],
                                className="six columns",
                            ),

                        ],
                        className="row ",
                    ),



                ],

            className="sub_page",
            ),
        ],
        className="page",
    )



#######################################################################################
# HELPERS
#######################################################################################


def Header(app, routes, active_route):
    return html.Div([get_header(app), html.Br([])])

def get_header(app):
    header = html.Div(
        [

            html.Div(
                [
                    html.Div(
                        [html.H5("NJ Bus Watcher")],
                        className="seven columns main-title",
                    ),

                    html.Div(
                        [
                            dcc.Link(
                                "FAQ",
                                href="/about",
                                className="full-view-link",
                            )
                        ],
                        className="five columns",
                    ),
                ],
                className="twelve columns",
                style={"padding-left": "0"},
            ),
        ],
        className="row",
    )
    return header



def get_route_menu(routes, active_route):


    # todo replace dropdown with a list of linked route #s each links to the URL /87 and active_route is populated by reading the URL
    # route_menu = html.Div(
    #     [
    #         dcc.Dropdown(
    #             id='route_choice',
    #             options=[{'label': '{} {}'.format(r,prettyname), 'value': r} for r,prettyname in routes.items()],
    #             value=active_route,
    #             clearable=False,
    #             style={'width': '60%'}
    #          )
    #     ],
    #     className="row",)

    route_html=[]
    for route in routes:
        route_html.append(dcc.Link(
            href='/{}'.format(route)
        ))
    route_menu = html.Div(
        [route_html]
    )


    return route_menu


def make_dash_table(df):
    """ Return a dash definition of an HTML table for a Pandas dataframe """
    table = []
    for index, row in df.iterrows():
        html_row = []
        for i in range(len(row)):
            html_row.append(html.Td([row[i]]))
        table.append(html.Tr(html_row))
    return table


def make_dash_chart_lines(df):
    fig = []
    data = go.Scatter(
            x=[x for x in (df.iloc[:, 0].tolist())],
            y=[y for y in (df.iloc[:, 1].tolist())],
            line={"color": "#e5bbed"},
            mode='lines',
            name="Weekdays",
        )
    fig.append(data)
    return fig

def make_dash_chart_bar(df):
    fig = []
    data = go.Bar(
            x=[x for x in (df.iloc[:, 0].tolist())],
            y=[y for y in (df.iloc[:, 1].tolist())],
             name="Weekdays",
        )
    fig.append(data)
    return fig

#
# def make_dash_chart_timeseries(df):
#     fig = []
#     data = go.Scatter(
#             x=df.hour,
#             y=[y for y in (df.iloc[:, 1].tolist())],
#              name="Weekdays",
#         )
#     fig.append(data)
#     return fig




if __name__ == "__main__":
    app.run_server(debug=True)
