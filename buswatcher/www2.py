# bus buswatcher v3.0
# todo rebuild the app a single-page app that updates based on your choices
# mar 2020 - by anthony@starcitygroup.us


import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import lib.DashHelpers as dh

from lib.TransitSystem import load_system_map


######################################### my logic

route=27
df_arrivals_by_hour=dh.get_arrivals_by_hour(route)


######################################### page template (dash bootstrap)
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Link", href="#")),
        dbc.DropdownMenu(
            nav=True,
            in_navbar=True,
            label="Menu",
            children=[
                dbc.DropdownMenuItem("Entry 1"),
                dbc.DropdownMenuItem("Entry 2"),
                dbc.DropdownMenuItem(divider=True),
                dbc.DropdownMenuItem("Entry 3"),
            ],
        ),
    ],
    brand="Demo",
    brand_href="#",
    sticky="top",
)

body = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H2("NJBusWatcher"),
                        html.P(
                            """\
Residents and businesses depend on NJTransit buses every day. But its hard to evaluate the quality of bus service. \
That's why we built this site to provide a one-stop shop for bus performance information. \
Here you can see data on past performance and view maps of current service."""
                        ),
                        dbc.Button("View details", color="secondary"),
                    ],
                    md=4,
                ),
                dbc.Col(
                    [
                        html.H2("Graph"),
                        dcc.Graph(id='arrival-histogram',
                                  figure={
                                      'data': [
                                          {'x': df_arrivals_by_hour.index, 'y': df_arrivals_by_hour['arrivals'],
                                           'type': 'bar', 'name': 'Arrivals'}
                                      ],
                                      'layout': {
                                          'title': 'Arrivals By Hour For A Route'
                                      }
                                  }
                                  ),
                    ]
                ),
            ]
        )
    ],
    className="mt-4",
)



######################################### app logic
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# todo add a callback with a dropdown to pick the route
app.layout = html.Div([navbar, body])




################################################
# MAIN SCRIPT
################################################

if __name__ == '__main__':
    system_map = load_system_map()
    app.run_server(debug=True)

# # after https://medium.com/@trstringer/logging-flask-and-gunicorn-the-manageable-way-2e6f0b8beb2f
# if __name__ != "__main__":
#     system_map = load_system_map()
#     gunicorn_logger = logging.getLogger("gunicorn.error")
#     app.logger.handlers = gunicorn_logger.handlers
#     app.logger.setLevel(gunicorn_logger.level)
