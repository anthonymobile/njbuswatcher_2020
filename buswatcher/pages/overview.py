import pandas as pd
import pathlib

import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go

from utils import Header, make_dash_table

import lib.Reports as reports
import lib.Maps as maps
# import lib.TransitSystem as system
# system_map = system.load_system_map()

# get relative data folder
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("../data").resolve()

# added by AT 17 march 2020
mapbox_access_token = 'pk.eyJ1IjoiYml0c2FuZGF0b21zIiwiYSI6ImNrN3dsb3Q1ODAzbTYzZHFwMzM4c2FmZjMifQ.HNRse1oELixf7zWOqVfbgA'


route = 87 #todo set this from the callback

_df_route_summary = reports.get_route_summary(route)
# todo plug in live data source by making a call to wwwAPI here e.g. df_route_summary = wwwAPI.get_route_summary(route) where route is a callback from a dropdown
_87_reliability_overview = pd.read_csv(DATA_PATH.joinpath("_87_reliability_overview.csv"))

# get current bus locations from NJTransit
map_data = maps.get_positions_byargs(route)

#  Layouts
# todo fix lat/lon center and zoom level using algo from old JS map?
layout_map = dict(
    autosize=True,
    height=500,
    font=dict(color="#191A1A"),
    titlefont=dict(color="#191A1A", size='14'),
    margin=dict(
        l=35,
        r=35,
        b=35,
        t=45
    ),
    hovermode="closest",
    plot_bgcolor='#fffcfc',
    paper_bgcolor='#fffcfc',
    legend=dict(font=dict(size=10), orientation='h'),
    title=str(route),
    mapbox=dict(
        accesstoken=mapbox_access_token,
        style="light",
        center=dict(
            lon=-74.042520,
            lat=40.750650
        ),
        zoom=10,
    )
)

# functions
def gen_map(map_data):
    return {
        "data": [{
                "type": "scattermapbox",
                "lat": list(map_data['lat']),
                "lon": list(map_data['lon']),
                "hoverinfo": "text",
                "hovertext": [["Route: {} <br>Vehicle: {} <br>Run: {}".format(i,j,k)]
                                for i,j,k in zip(map_data['rt'], map_data['id'],map_data['run'])],
                "mode": "markers",
                "name": list(map_data['id']),
                "marker": {
                    "size": 6,
                    "opacity": 0.7
                }
        }],
        "layout": layout_map
    }



def create_layout(app,routes):
    # Page layouts
    return html.Div(
        [
            html.Div([Header(app,routes)]),
            # page 1
            html.Div(
                [
                    # Row 1
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.H5("How Is the 87 Doing?"), # todo inject callback here
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
                                ],
                                className="six columns",
                            ),
                            html.Div(
                                [
                                    html.H6(
                                        "Overall Grade", className="subtitle padded"
                                    ),
                                    html.Img(
                                        src=app.get_asset_url("risk_reward.png"),
                                        className="risk-reward",
                                    ),
                                ],
                                className="six columns",
                            ),
                        ],
                        className="row ",
                    ),


                    # Row 3
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
                                            "data": [
                                                go.Scatter(
                                                    x=[
                                                        "6",
                                                        "7",
                                                        "8",
                                                        "9",
                                                        "10",
                                                        "11",
                                                        "12",
                                                        "13",
                                                        "14",
                                                        "15",
                                                        "16",
                                                    ],
                                                    y=[
                                                        "20",
                                                        "20",
                                                        "8",
                                                        "7",
                                                        "5",
                                                        "16",
                                                        "22",
                                                        "25",
                                                        "8",
                                                        "4",
                                                        "2",
                                                    ],
                                                    line={"color": "#e5bbed"},
                                                    mode="lines",
                                                    name="87 Weekdays",
                                                )
                                            ],
                                            "layout": go.Layout(
                                                autosize=True,
                                                title="",
                                                font={"family": "Raleway", "size": 10},
                                                height=200,
                                                width=340,
                                                hovermode="closest",
                                                legend={
                                                    "x": -0.0277108433735,
                                                    "y": -0.142606516291,
                                                    "orientation": "h",
                                                },
                                                margin={
                                                    "r": 20,
                                                    "t": 20,
                                                    "b": 20,
                                                    "l": 50,
                                                },
                                                showlegend=True,
                                                xaxis={
                                                    "autorange": True,
                                                    "linecolor": "rgb(0, 0, 0)",
                                                    "linewidth": 1,
                                                    "range": [6, 16],
                                                    "showgrid": False,
                                                    "showline": True,
                                                    "title": "",
                                                    "type": "linear",
                                                },
                                                yaxis={
                                                    "autorange": False,
                                                    "gridcolor": "rgba(127, 127, 127, 0.2)",
                                                    "mirror": False,
                                                    "nticks": 4,
                                                    "range": [0, 30],
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

                                    html.H6(
                                        "Reliability",
                                        className="subtitle padded",
                                    ),
                                    dcc.Graph(
                                        id="graph-2",
                                        figure={
                                            "data": [
                                                go.Scatter(
                                                    x=[
                                                        "6",
                                                        "7",
                                                        "8",
                                                        "9",
                                                        "10",
                                                        "11",
                                                        "12",
                                                        "13",
                                                        "14",
                                                        "15",
                                                        "16",
                                                    ],
                                                    y=[
                                                        "65",
                                                        "65",
                                                        "75",
                                                        "95",
                                                        "75",
                                                        "65",
                                                        "65",
                                                        "75",
                                                        "95",
                                                        "75",
                                                        "65",
                                                    ],
                                                    line={"color": "#e5bbed"},
                                                    mode="lines",
                                                    name="87 Weekdays",
                                                )
                                            ],
                                            "layout": go.Layout(
                                                autosize=True,
                                                title="",
                                                font={"family": "Raleway", "size": 10},
                                                height=200,
                                                width=340,
                                                hovermode="closest",
                                                legend={
                                                    "x": -0.0277108433735,
                                                    "y": -0.142606516291,
                                                    "orientation": "h",
                                                },
                                                margin={
                                                    "r": 20,
                                                    "t": 20,
                                                    "b": 20,
                                                    "l": 50,
                                                },
                                                showlegend=True,
                                                xaxis={
                                                    "autorange": True,
                                                    "linecolor": "rgb(0, 0, 0)",
                                                    "linewidth": 1,
                                                    "range": [6, 16],
                                                    "showgrid": False,
                                                    "showline": True,
                                                    "title": "",
                                                    "type": "linear",
                                                },
                                                yaxis={
                                                    "autorange": False,
                                                    "gridcolor": "rgba(127, 127, 127, 0.2)",
                                                    "mirror": False,
                                                    "nticks": 4,
                                                    "range": [0, 120],
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







                                    # html.Div(
                                    #     [
                                    #         html.H6(
                                    #             "Reliability",
                                    #             className="subtitle padded",
                                    #         ),
                                    #         html.Table(make_dash_table(_87_reliability_overview)),
                                    #     ],
                                    #     className="twelve columns",
                                    # ),
                                ],
                                className="six columns",
                            ),
                            html.Div(
                                [
                            html.H6(
                                "Route Map",
                                className="subtitle padded",
                            ),
                            # good spot for the map
                            dcc.Graph(id="map", config={"responsive": True},
                                      figure=gen_map(map_data)
                                    ),


                        ],
                        className="six columns",
                    ),


                        ],
                        className="row ",
                    ),

                    # # Row 4
                    # html.Div(
                    #     [
                    #         html.Div(
                    #             [
                    #                 html.H6(
                    #                     "Reliability",
                    #                     className="subtitle padded",
                    #                 ),
                    #                 html.Table(make_dash_table(_df_reliability_overview)),
                    #             ],
                    #             className="six columns",
                    #         ),
                    #
                    #     ],
                    #     className="row ",
                    # ),
                ],

            className="sub_page",
            ),
        ],
        className="page",
    )
