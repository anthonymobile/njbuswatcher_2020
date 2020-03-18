import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import lib.wwwAPI as api

from utils import Header, make_dash_table

import pandas as pd
import pathlib

# get relative data folder
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("../data").resolve()

# added by AT 17 march 2020
mapbox_token = "pk.eyJ1IjoiYml0c2FuZGF0b21zIiwiYSI6ImNrN3dsb3Q1ODAzbTYzZHFwMzM4c2FmZjMifQ.HNRse1oELixf7zWOqVfbgA"


# todo plug in live data source by making a call to wwwAPI here e.g. df_route_summary = wwwAPI.get_route_summary(route) where route is a callback from a dropdown
route = 87
_df_route_summary = api.get_route_summary(route)
_df_reliability_overview = pd.read_csv(DATA_PATH.joinpath("_df_reliability_overview.csv"))



# todo replace with API call (and move those routines into wwwAPI
# get data
buses = pd.read_csv(DATA_PATH.joinpath("_df_87_buses.csv"), low_memory=False)

# from https://github.com/plotly/dash-sample-apps/blob/master/apps/dash-spatial-clustering/app.py


# 
# geo_colors = [
#     "#8dd3c7",
#     "#ffd15f",
#     "#bebada",
#     "#fb8072",
#     "#80b1d3",
#     "#fdb462",
#     "#b3de69",
#     "#fccde5",
#     "#d9d9d9",
#     "#bc80bd",
#     "#ccebc5",
# ]

# def make_base_map():
#     # Scattermapbox with geojson layer, plot all listings on mapbox
#     customdata = list(
#         zip(
#             buses["rt"],
#             buses["v"],
#             buses["trip"],
#         )
#     )
#     mapbox_figure = dict(
#         type="scattermapbox",
#         lat=buses["lat"],
#         lon=buses["lon"],
#         marker=dict(size=7, opacity=0.7, color="#550100"),
#         customdata=customdata,
#         name="Buses",
#         hovertemplate="<b>Route: %{customdata[0]}</b><br><br>"
#         "<b>Vehicle No.: %{customdata[1]}</b><br>"
#         "<b>Trip No.: </b>%{customdata[2]}<br>",
#     )
# 
#     layout = dict(
#         mapbox=dict(
#             style="streets",
#             uirevision=True,
#             accesstoken=mapbox_token,
#             zoom=9,
#             center=dict(
#                 lon=buses["lon"].mean(),
#                 lat=buses["lat"].mean(),
#             ),
#         ),
#         shapes=[
#             {
#                 "type": "rect",
#                 "xref": "paper",
#                 "yref": "paper",
#                 "x0": 0,
#                 "y0": 0,
#                 "x1": 1,
#                 "y1": 1,
#                 "line": {"width": 1, "color": "#B0BEC5"},
#             }
#         ],
#         margin=dict(l=10, t=10, b=10, r=10),
#         height=400,
#         showlegend=False,
#         hovermode="closest",
#     )
# 
#     figure = {"data": [mapbox_figure], "layout": layout}
#     return figure



def create_layout(app,routes):
    # Page layouts
    return html.Div(
        [
            html.Div([Header(app,routes)]),
            # page 1
            html.Div(
                [
                    # Row 3
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.H5("How Is the 87 Doing?"),
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

                    # Row 4
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.H6(
                                        ["Key Indicators"], className="subtitle padded"
                                    ),
                                    html.Table(make_dash_table(_df_route_summary)),
                                ],
                                className="six columns",
                            ),
                            # todo redo layout to restore column break here
                            html.Div(
                                [

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
                        className="row",
                        style={"margin-bottom": "35px"},
                    ),
                    # Row 5
                    # todo this row dissappeared?
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
                                                        "2008",
                                                        "2009",
                                                        "2010",
                                                        "2011",
                                                        "2012",
                                                        "2013",
                                                        "2014",
                                                        "2015",
                                                        "2016",
                                                        "2017",
                                                        "2018",
                                                    ],
                                                    y=[
                                                        "10000",
                                                        "7500",
                                                        "9000",
                                                        "10000",
                                                        "10500",
                                                        "11000",
                                                        "14000",
                                                        "18000",
                                                        "19000",
                                                        "20500",
                                                        "24000",
                                                    ],
                                                    line={"color": "#e5bbed"},
                                                    mode="lines",
                                                    name="Calibre Index Fund Inv",
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
                                                    "range": [2008, 2018],
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
                                                    "range": [0, 30000],
                                                    "showgrid": True,
                                                    "showline": True,
                                                    "ticklen": 10,
                                                    "ticks": "outside",
                                                    "title": "$",
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

                            html.H6(
                                "Route Map",
                                className="subtitle padded",
                            ),
                            # good spot for the map
                            dcc.Graph(id="map", config={"responsive": True}),

                            # dcc.Graph(
                            #     id="graph-1",
                            #     figure={
                            #         "data": [
                            #             go.Bar(
                            #                 x=[
                            #                     "1 Year",
                            #                     "3 Year",
                            #                     "5 Year",
                            #                     "10 Year",
                            #                     "41 Year",
                            #                 ],
                            #                 y=[
                            #                     "21.67",
                            #                     "11.26",
                            #                     "15.62",
                            #                     "8.37",
                            #                     "11.11",
                            #                 ],
                            #                 marker={
                            #                     "color": "#e5bbed",
                            #                     "line": {
                            #                         "color": "rgb(255, 255, 255)",
                            #                         "width": 2,
                            #                     },
                            #                 },
                            #                 name="NJ Bus Watcher",
                            #             ),
                            #             go.Bar(
                            #                 x=[
                            #                     "1 Year",
                            #                     "3 Year",
                            #                     "5 Year",
                            #                     "10 Year",
                            #                     "41 Year",
                            #                 ],
                            #                 y=[
                            #                     "21.83",
                            #                     "11.41",
                            #                     "15.79",
                            #                     "8.50",
                            #                 ],
                            #                 marker={
                            #                     "color": "#dddddd",
                            #                     "line": {
                            #                         "color": "rgb(255, 255, 255)",
                            #                         "width": 2,
                            #                     },
                            #                 },
                            #                 name="S&P 500 Index",
                            #             ),
                            #         ],
                            #         "layout": go.Layout(
                            #             autosize=False,
                            #             bargap=0.35,
                            #             font={"family": "Raleway", "size": 10},
                            #             height=200,
                            #             hovermode="closest",
                            #             legend={
                            #                 "x": -0.0228945952895,
                            #                 "y": -0.189563896463,
                            #                 "orientation": "h",
                            #                 "yanchor": "top",
                            #             },
                            #             margin={
                            #                 "r": 0,
                            #                 "t": 20,
                            #                 "b": 10,
                            #                 "l": 10,
                            #             },
                            #             showlegend=True,
                            #             title="",
                            #             width=330,
                            #             xaxis={
                            #                 "autorange": True,
                            #                 "range": [-0.5, 4.5],
                            #                 "showline": True,
                            #                 "title": "",
                            #                 "type": "category",
                            #             },
                            #             yaxis={
                            #                 "autorange": True,
                            #                 "range": [0, 22.9789473684],
                            #                 "showgrid": True,
                            #                 "showline": True,
                            #                 "title": "",
                            #                 "type": "linear",
                            #                 "zeroline": False,
                            #             },
                            #         ),
                            #     },
                            #     config={"displayModeBar": False},
                            # ),
                        ],
                        className="six columns",
                    ),

                            html.Div(
                                [
                                    html.H6(
                                        "Reliability",
                                        className="subtitle padded",
                                    ),
                                    html.Table(make_dash_table(_df_reliability_overview)),
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
