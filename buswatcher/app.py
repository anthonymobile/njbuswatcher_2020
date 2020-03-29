# -*- coding: utf-8 -*-

from pathlib import Path
import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Input, Output
from lib.TransitSystem import load_system_map
import lib.Maps as maps


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


# Update page
@app.callback(
        Output("page-content", "children"),
        [Input("url", "pathname")])
def display_page(pathname):

    if pathname is None:
        return 'Loading...'
    elif pathname == '/':
        active_route='87'
        return create_layout(app, routes, active_route)
    else:
        active_route=(pathname[1:])
        return create_layout(app, routes, active_route)


def create_layout(app, routes, active_route):

    # load data
    _df_route_summary = get_report(active_route,"summary")

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

                                    # dcc.Graph(id="map", config={"responsive": True},
                                    #           figure=maps.gen_map(active_route)
                                    #           ),
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
                                            "data": make_chart_bar(get_report(active_route, "frequency")),

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
                                            "data": make_chart_bar(get_report(active_route, "reliability")),

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

                    # Row 3
                    html.Div(
                        [

                            html.Div(
                                [
                                    html.H6(
                                        "Bunching Report",
                                        className="subtitle padded",
                                    ),
                                    dcc.Graph(
                                        figure=make_curve_and_rug_plot(get_report(active_route, "bunching"))),

                                    html.Br([]),

                                ],

                                className="twelve columns",
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

# future these can also call the Generator explicitly and ask for a df response
# report loader function
def get_report(route,report):
    PATH = Path(__file__).parent
    # DATA_PATH = PATH.joinpath("../data").resolve()
    DATA_PATH = PATH.joinpath("data").resolve()
    return pd.read_csv('{}/{}_{}.csv'.format(DATA_PATH,route,report), quotechar='"')


def get_route_menu(routes, active_route):
    ## future restore old dropdown version
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

    # todo cleanup display of routes in header block
    route_html=[]
    for route in routes:
        route_html.append(dcc.Link('{}•'.format(route), href='/{}'.format(route)
        ))
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


def make_chart_lines(df):
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

def make_chart_bar(df):
    fig = []
    data = go.Bar(
            x=[x for x in (df.iloc[:, 0].tolist())],
            y=[y for y in (df.iloc[:, 1].tolist())],
             name="Weekdays",
        )
    fig.append(data)
    return fig

def make_curve_and_rug_plot(df):

    # TEST DUMMY CURVE
    # https://plotly.com/python/distplot/
    # assumes that data is distance of each bunching incident on the route from the start
    # format of csv/df
    # period1_label,period2_label,period3_label
    # 23,12,23
    #
    #
    import numpy as np
    import plotly.figure_factory as ff

    period1_data = np.random.randn(100) -1
    period2_data = np.random.randn(100)
    period3_data = np.random.randn(100) +1

    hist_data = [period1_data, period2_data, period3_data]
    group_labels = ['Weekdays', 'Weekends', 'Late Night']
    colors = ['#333F44', '#37AA9C', '#94F3E4']

    fig = ff.create_distplot(hist_data, group_labels, show_hist=False, colors=colors)

    return fig

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


if __name__ == "__main__":
    app.run_server(debug=True)
