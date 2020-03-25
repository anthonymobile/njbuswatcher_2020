# import json
# import geojson
import pandas as pd
from lib.TransitSystem import load_system_map

from . import NJTransitAPI as njt

# added by AT 17 march 2020
mapbox_access_token = 'pk.eyJ1IjoiYml0c2FuZGF0b21zIiwiYSI6ImNrN3dsb3Q1ODAzbTYzZHFwMzM4c2FmZjMifQ.HNRse1oELixf7zWOqVfbgA'

system_map=load_system_map()

# generate the map code for dash Graph
#todo add another dictionary in the data list for the routes
'''

"data": [{
                "type": "scattermapbox",...
                },


'''


def gen_map(route):
    bus_positions = get_bus_positions(route)
    route_waypoints = get_route_waypoints(route)

    return {
        "data": [

            {
                "type": 'scattermapbox',
                "lat": list(route_waypoints['lat']),
                "lon": list(route_waypoints['lon']),
                "mode": "lines",
                "line": {
                    "width": "3",
                    "color": "blue"
                }
            },

            {
                "type": "scattermapbox",
                "lat": list(bus_positions['lat']),
                "lon": list(bus_positions['lon']),
                "hoverinfo": "text",
                "hovertext": [["Route: {} <br>Vehicle: {} <br>Run: {}".format(i,j,k)]
                                for i,j,k in zip(bus_positions['rt'], bus_positions['id'],bus_positions['run'])],
                "mode": "markers",
                "name": list(bus_positions['id']),
                "marker": {
                    "size": 10,
                    "opacity": 0.7,
                    "color": "#f6c"

                },

        }



        ],
        "layout": layout_map(bus_positions)
    }


# template for layout


def layout_map(map_data):

    center_lat = sum(map_data['lat'])/len(map_data['lat'])
    center_lon = sum(map_data['lon']) / len(map_data['lon'])

    # todo suppress hovermode for the line layer
    # future dynamic zoom level to extent of bus locations with turf.js
    # in JavaScript: map.fitBounds(turf.bbox(map_data), {padding: 50});

    layout_map = dict(
        autosize=True,
        height=340,
        width=340,
        font=dict(color="#191A1A"),
        titlefont=dict(color="#191A1A", size='14'),
        margin=dict(
            l=3,
            r=3,
            b=3,
            t=3
        ),
        hovermode="closest",
        plot_bgcolor='#fffcfc',
        paper_bgcolor='#fffcfc',
        showlegend=False,
        mapbox=dict(
            accesstoken=mapbox_access_token,
            style="light",
            center=dict(
                lon=center_lon,
                lat=center_lat
            ),
            zoom=11,
        )
    )

    return layout_map


# get route geometry
def get_route_waypoints(route):
    # test_data = {'lat': [45, 46, 47], 'lon': [-72,-71,-70]}
    # route_waypoints=pd.DataFrame.from_dict(test_data)
    # return route_waypoints

    # get waypoints and unzip
    lat, lon = zip(*system_map.route_geometries[str(route)]['coordinate_bundle']['waypoints_coordinates'])
    route_waypoints = {'lat': lat, 'lon': lon}
    return route_waypoints




# get bus positions for route as a df
def get_bus_positions(route):
    positions = njt.parse_xml_getBusesForRoute(njt.get_xml_data('nj', 'buses_for_route', route=route))
    labels = ['lat', 'lon', 'id', 'run']
    positions_log=pd.DataFrame(columns=labels)
    for bus in positions:
        update = dict()
        for key,value in vars(bus).items():
            if key in labels:
                if key == 'lat' or key == 'lon':
                    value = float(value)
                update[key] = value
        update['rt'] = str(route)
        positions_log = positions_log.append(update,ignore_index=True)
    try:
        positions_log = positions_log.set_index('timestamp',drop=False)
    except:
        pass
    return positions_log

