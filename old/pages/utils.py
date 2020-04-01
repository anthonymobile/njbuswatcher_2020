import json

import dash_html_components as html
import dash_core_components as dcc
import plotly.graph_objs as go


def Header(app,routes,active_route):
    return html.Div([get_header(app), html.Br([]), get_dropdown(routes,active_route),html.Br([]), get_menu()])


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
                                "Full View",
                                href="/full-view",
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


def get_menu():
    menu = html.Div(
        [
            dcc.Link(
                "Overview",
                href="/overview",
                className="tab first",
            ),
            dcc.Link(
                "Speed",
                href="/speed",
                className="tab",
            ),
            dcc.Link(
                "Frequency",
                href="/frequency",
                className="tab",
            ),
            dcc.Link(
                "Reliability",
                href="/reliability",
                className="tab"
            ),
            dcc.Link(
                "Bunching",
                href="/bunching",
                className="tab",
            ),
            dcc.Link(
                "News & Reviews",
                href="/news-and-reviews",
                className="tab",
            ),

            html.H5(id="active_route"),

        ],
        className="row all-tabs",
    )
    return menu


def get_dropdown(routes,active_route):

    # default route to start
    if active_route is None:
        active_route = '87'


    dropdown = html.Div(
        [
            dcc.Dropdown(
                id='route_choice',
                options=[{'label': '{} {}'.format(r,prettyname), 'value': r} for r,prettyname in routes.items()],
                value=active_route
             )
        ],
        className="row",)

    # dropdown = html.Div(
    #     [
    #         dcc.Dropdown(
    #             id='route_choice',
    #             options=[{'label': '{} {}'.format(r,prettyname), 'value': r} for r,prettyname in routes.items()],
    #             value='87',
    #         )
    #     ],
    #     className="row",)

        # style={'width': '48%', 'display': 'inline-block'})

    return dropdown


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