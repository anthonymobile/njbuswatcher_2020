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
app = dash.Dash( __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}],external_stylesheets=[dbc.themes.FLATLY])
server = app.server
app.config['suppress_callback_exceptions'] = True # # suppress callback warnings

# basic structure for callback
app.layout = html.Div(
                        [
                            dcc.Location(id="url", refresh=False),
                            html.Div(id="page-content")
                        ]
                      )

# callback implementation
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



'''
# layout
def create_layout(app, routes_watching, active_route):

    # load data
    _df_route_summary = get_report(active_route,"summary")

    # Page layouts
    return 
        
        
        
        html.Div(
        [
            Header(app, routes_watching, active_route),
            # page 1
            html.Div(
                [
                    # Row 1
                    html.Div(
                        [
                            html.Div(
                                [
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
                                    get_route_menu(routes_watching, active_route),


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
                                        ["How Well Does this Route Work?"], className="subtitle padded"
                                    ),
                                    html.P('Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula eget dolor. \
                                    Aenean massa. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. \
                                    Donec quam felis, ultricies nec, pellentesque eu, pretium quis, sem. Nulla consequat massa quis enim.',
                                           ),
                                    # html.Table(make_dash_table(_df_route_summary)),
                                    html.Br([]),
                                ],
                                className="twelve columns",
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
                                        "Where Does the {} Go? ".format(active_route),
                                        className="subtitle padded",
                                    ),

                                    # dcc.Graph(id="map", config={"responsive": True},
                                    #           figure=maps.gen_map(active_route)
                                    #           ),
                                    html.Br([]),

                                ],

                                className="twelve columns",
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
                                        "How Often Do Buses Arrive?",
                                        className="subtitle padded",
                                    ),
                                    html.P('Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula eget dolor. \
                                    Aenean massa. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. \
                                    Donec quam felis, ultricies nec, pellentesque eu, pretium quis, sem. Nulla consequat massa quis enim',
                                    ),
                                ],

                                className="six columns",
                            ),
                            html.Div(
                                [
                                    html.H6(
                                        "How Reliable Is Travel Time?",
                                        className="subtitle padded",
                                    ),
                                    html.P('Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula eget dolor. \
                                            Aenean massa. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. \
                                            Donec quam felis, ultricies nec, pellentesque eu, pretium quis, sem. Nulla consequat massa quis enim',
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
                                    # html.H6(
                                    #     "How Often Do Buses Arrive?",
                                    #     className="subtitle padded",
                                    # ),
                                    # html.P('Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula eget dolor. \
                                    # Aenean massa. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. \
                                    # Donec quam felis, ultricies nec, pellentesque eu, pretium quis, sem. Nulla consequat massa quis enim',
                                    # ),
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
                                    dcc.Graph(
                                        figure=make_chart_line_new(get_report(active_route, "reliability"))),

                                    html.Br([]),

                                    # html.H6(
                                    #     "How Reliable Is Travel Time?",
                                    #     className="subtitle padded",
                                    # ),
                                    # html.P('Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula eget dolor. \
                                    #         Aenean massa. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. \
                                    #         Donec quam felis, ultricies nec, pellentesque eu, pretium quis, sem. Nulla consequat massa quis enim',
                                    #        ),
                                    # dcc.Graph(
                                    #                                     #     id="graph-2",
                                    #                                     #     figure={
                                    #                                     #         "data": make_chart_line(get_report(active_route, "reliability")),
                                    #                                     #
                                    #                                     #         "layout": go.Layout(
                                    #                                     #             autosize=True,
                                    #                                     #             title="",
                                    #                                     #             font={"family": "Raleway", "size": 10},
                                    #                                     #             height=200,
                                    #                                     #             width=340,
                                    #                                     #             hovermode="closest",
                                    #                                     #             margin={
                                    #                                     #                 "r": 20,
                                    #                                     #                 "t": 20,
                                    #                                     #                 "b": 40,
                                    #                                     #                 "l": 50,
                                    #                                     #             },
                                    #                                     #             showlegend=False,
                                    #                                     #             xaxis={
                                    #                                     #                 "autorange": True,
                                    #                                     #                 "linecolor": "rgb(0, 0, 0)",
                                    #                                     #                 "linewidth": 1,
                                    #                                     #                 "range": [6, 16],
                                    #                                     #                 "showgrid": False,
                                    #                                     #                 "showline": True,
                                    #                                     #                 "title": "hour of day",
                                    #                                     #                 "type": "linear",
                                    #                                     #             },
                                    #                                     #             yaxis={
                                    #                                     #                 "autorange": False,
                                    #                                     #                 "gridcolor": "rgba(127, 127, 127, 0.2)",
                                    #                                     #                 "mirror": False,
                                    #                                     #                 "nticks": 4,
                                    #                                     #                 "range": [0, 150],
                                    #                                     #                 "showgrid": True,
                                    #                                     #                 "showline": True,
                                    #                                     #                 "ticklen": 10,
                                    #                                     #                 "ticks": "outside",
                                    #                                     #                 "title": "minutes",
                                    #                                     #                 "type": "linear",
                                    #                                     #                 "zeroline": False,
                                    #                                     #                 "zerolinewidth": 4,
                                    #                                     #             },
                                    #                                     #         ),
                                    #                                     #     },
                                    #                                     #     config={"displayModeBar": False},
                                    #                                     # ),



                                ],
                                className="six columns",
                            ),

                        ],
                        className="row ",
                    ),

                    # Row 4
                    html.Div(
                        [

                            html.Div(
                                [


                                    html.H6(
                                        "Where Are the Bottlenecks?",
                                        className="subtitle padded",
                                    ),
                                    html.P('Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula eget dolor. \
    Aenean massa. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. \
    Donec quam felis, ultricies nec, pellentesque eu, pretium quis, sem. Nulla consequat massa quis enim',
                                           ),
                                    html.Br([]),
                                    # dcc.Graph(
                                    #     figure=make_curve_and_rug_plot(active_route)),
                                    #
                                    # html.Br([]),
                                    dcc.Graph(
                                        figure=make_ridgeline_plot(active_route)),

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

    '''






#######################################################################################
# __MAIN__
#######################################################################################
if __name__ == "__main__":
    app.run_server(debug=True)
