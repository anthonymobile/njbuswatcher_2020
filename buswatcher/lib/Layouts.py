# -*- coding: utf-8 -*-

from pathlib import Path
import pandas as pd
from sklearn.datasets import make_blobs
import random
import numpy as np

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

import plotly.graph_objs as go
import plotly.figure_factory as ff
from plotly.colors import n_colors
import plotly.express as px

import lib.Maps as maps
from lib.TransitSystem import load_system_map


### GET buswatcher CONFIG
# get system map
system_map=load_system_map()

def create_layout(app, routes_watching, active_route):

    return html.Div(
        [
            dbc.Container(

                [


                dbc.Row(
                    [
                        dbc.Col(

                            html.H5('Column1')
                        ),
                        dbc.Col(

                            html.H5('Column2')
                        ),
                        dbc.Col(

                            html.H5('Column3')
                        )
                    ]
                ),

                dbc.Row(
                    [
                        dbc.Col(

                            html.H5('Column1')
                        ),
                        dbc.Col(

                            html.H5('Column2')
                        ),
                        dbc.Col(

                            html.H5('Column3')
                        )
                    ]
                )

                    ]


            )

        ]
    )



#######################################################################################
# HELPERS
#######################################################################################
# future these can also call the Generator explicitly and ask for a df response
# report loader function

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


def get_report(route, report):
    PATH = Path(__file__).parent
    # DATA_PATH = PATH.joinpath("../data").resolve()
    DATA_PATH = PATH.joinpath("data").resolve()

    if report == "summary":  # todo then generate on the fly, pulling together various pieces of data
        # from route_desciptions.json:
        #       origin, destination, geometry statistics=distance between stops, turns per mile (todo in TransitSystem)
        # from travel_time? #todo Generators
        #       average speed
        # from a new all-routes-grades.csv file (todo in Generators)
        #       overall_grade

        summary_template = {
            'label': 'value',
            'Route number': '87',
            'Origin': 'Summary Template',
            'Destination': 'Summary Template',
            'Average Speed': '9.8 mph',
            'Distance between stops': '750',
            'Turns per mile': '2.1',
            'Overall grade': 'D',
            'Notes': 'Summary Template'
        }

        return pd.DataFrame.from_dict(summary_template, orient='index')

    else:
        return pd.read_csv('{}/{}_{}.csv'.format(DATA_PATH, route, report), quotechar='"')


def get_route_menu(routes, active_route):
    # todo cleanup display of route menu, possibly move
    # future restore the dropdown menu?
    route_html = []
    for route in routes:
        route_html.append(dcc.Link(html.Button(route, className="button-route"), href='/{}'.format(route)))

    route_menu = html.Div(
        route_html
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


def make_chart_line_new(df):
    fig = px.line(df, x="hour", y=" minutes", title='End-to-End Travel time')

    fig.update_layout(autosize=True,
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
                          "title": "",
                          "type": "linear",
                      },
                      yaxis={
                          "autorange": False,
                          "gridcolor": "rgba(127, 127, 127, 0.2)",
                          "mirror": False,
                          "nticks": 4,
                          "range": [0, 150],
                          "showgrid": True,
                          "showline": True,
                          "ticklen": 10,
                          "ticks": "outside",
                          "title": "minutes",
                          "type": "linear",
                          "zeroline": False,
                          "zerolinewidth": 4,
                      },
                      )

    fig.update_xaxes(
        ticktext=["6am", "12pm", "6pm"],
        tickvals=['6', '12', '18'],
    )

    return fig


def make_chart_line(df):  # todo making a line chart look good requires a lot of data points (every 10 mins all day)
    fig = []
    data = go.Scatter(
        x=[x for x in (df.iloc[:, 0].tolist())],
        y=[y for y in (df.iloc[:, 1].tolist())],
        line={"color": "#e5bbed"},
        mode='lines',
        name="Weekdays",
    )

    fig.append(data)

    # # todo filled lines / bands
    # https://plotly.com/python/line-charts/#filled-lines

    return fig


def make_chart_bar(df):
    fig = []
    data = go.Bar(
        x=[x for x in (df.iloc[:, 0].tolist())],
        y=[y for y in (df.iloc[:, 1].tolist())],
        name="Weekdays",
    )
    fig.append(data)
    return fig


def make_curve_and_rug_plot(route):
    # TEST DUMMY CURVE
    # https://plotly.com/python/distplot/
    # assumes that data is distance of each bunching incident on the route from the start

    periods, data, colors = get_bunching_sample_data(route)

    fig = ff.create_distplot(data, periods, show_hist=False, colors=colors)

    fig.update_layout(
        autosize=False,
        width=700,
        height=200,
        margin=dict(
            l=10,
            r=10,
            b=10,
            t=10,
            pad=4
        ),
        paper_bgcolor="White",
        font=dict(
            family="Garamond",
            size=12,
            color="#000000"
        )
    )

    # todo add enumerated labels with stop names -- https://plotly.com/python/axes/#enumerated-ticks-with-tickvals-and-ticktext

    # Set custom x-axis labels
    fig.update_xaxes(
        ticktext=["Journal Square", "Palisade Av + Franklin Av", "Hoboken Terminal"],
        tickvals=['0', '12500', '25000'],
    )
    #
    # fig.update_xaxes(
    #     ticktext=["a", "b", "c","d","e"],
    #     tickvals=['0','5000','10000','12500','25000'],
    # )

    fig.update_yaxes(showticklabels=False)

    return fig


def make_ridgeline_plot(route):
    periods, data, colors = get_bunching_sample_data(route)

    fig = go.Figure()

    for data_line, color, period in zip(data, colors, periods):
        fig.add_trace(go.Violin(x=data_line, line_color=color, name=period))

    fig.update_traces(orientation='h', side='positive', width=3, points=False)
    fig.update_layout(xaxis_showgrid=False, xaxis_zeroline=False)

    # Set custom x-axis labels
    fig.update_xaxes(
        ticktext=["Journal Square", "Palisade Av + Franklin Av", "Hoboken Terminal"],
        tickvals=['0', '12500', '25000'],
    )

    # fig.update_xaxes(showticklabels=False)
    fig.update_yaxes(showticklabels=False)

    fig.update_layout(
        # legend_orientation="h",
        autosize=True,
        width=720,
        height=400,
        margin=dict(
            l=0,
            r=0,
            b=0,
            t=0,
            pad=0
        ),
        paper_bgcolor="White",
        font=dict(
            family="Garamond",
            size=12,
            color="#000000"
        )
    )

    fig.update_layout(
        legend=dict(
            traceorder="reversed"
        )
    )

    fig.update_xaxes(range=[0, 25000])

    return fig


def get_bunching_sample_data(route):
    # get sample data
    PATH = Path(__file__).parent
    # DATA_PATH = PATH.joinpath("../data").resolve()
    DATA_PATH = PATH.joinpath("data").resolve()

    periods = ['am', 'midday', 'pm', 'late', 'weekends']
    data = []
    for period in periods:
        ## load data from CSV
        # data.append(np.loadtxt('{}/{}_{}_{}.csv'.format(DATA_PATH, route, "bunching", period), skiprows=1))

        # generate random data
        n_centers = 50  # no of bunching points
        bunches, y = make_blobs(n_samples=random.randint(1, 501), centers=n_centers, n_features=1,
                                center_box=(0.0, 25000))
        data.append(bunches.flatten())

    colors = n_colors('rgb(5, 200, 200)', 'rgb(200, 10, 10)', 5, colortype='rgb')
    return periods, data, colors
