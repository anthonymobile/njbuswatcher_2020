# bus buswatcher v3.0
# mar 2020 - by anthony@starcitygroup.us


import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import lib.DashHelpers as dh

from lib.TransitSystem import load_system_map


######################################### my logic

route=27
df_arrivals_by_hour=dh.get_arrivals_hourly_histogram(route)


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
    brand="NJBusWatcher",
    brand_href="#",
    sticky="top",
)

body = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H1("How Are New Jersey's Buses Doing Today?"),
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
                        html.H3("When Did Buses Arrive Today?"),
                        # todo change this to a scatterplot showing exact time for each arrival(x) vs headway(y) using dh.get_arrivals_today_all
                        dcc.Graph(id='arrival-histogram',
                                  figure={
                                      'data': [
                                          {'x': df_arrivals_by_hour.index, 'y': df_arrivals_by_hour['arrivals'],
                                           'type': 'bar', 'name': 'Arrivals'}
                                      ],
                                      'layout': {
                                          'title': 'Arrivals By Hour For A Route (today)'
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
