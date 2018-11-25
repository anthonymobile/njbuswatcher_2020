mapboxgl.accessToken = 'pk.eyJ1IjoiYml0c2FuZGF0b21zIiwiYSI6ImNqbDhvZnl1YjB4NHczcGxsbTF6bWRjMWQifQ.w2TI_q7ClI4JE5I7QU3hEA';
var map = new mapboxgl.Map({
    container: 'map',
    style: "mapbox://styles/mapbox/light-v9",
    zoom: 0
});


map.on('load', function() {

    // starting view
    var mapCoordinates = [40.7400, -74.0501];
    var mapZoom = 13;

    // ROUTES
    var waypoints_geojson = {
        'type': 'geojson',
        'data': passed_citywide_waypoints_geojson
    };

    map.addSource('waypoints_geojson', waypoints_geojson);

    map.addLayer({
        "id": "route",
        "type": "line",
        "source": "waypoints_geojson",
        "paint": {
            "line-color": "blue",
            "line-opacity": 0.5,
            "line-width": 3
        }

    });

    // STOPS
    var stops_geojson = {
        type: 'geojson',
        data: passed_citywide_stops_geojson
    };

    map.addSource('stops_geojson', stops_geojson);

    map.addLayer({
        "id": "stops",
        "type": "circle",
        "source": "stops_geojson",
        "paint": {
            "circle-radius": 2,
            "circle-opacity": 1,
            "circle-stroke-width": 1,
            "circle-stroke-color": "#fff"
        }
    });


    // VEHICLES
    var routelistArray=passed_reportcard_routes;

    for(let j=0; j<routelistArray.length; j++) {

        var url = ('/api/v1/positions?period=now&rt='+routelistArray[j].route);

        map.addSource('vehicles_geojson'+routelistArray[j].route, {
            type: 'geojson',
            data: url
        });

        map.addLayer({
        "id": "vehicles"+routelistArray[j].route,
        "type": "circle",
        "source": "vehicles_geojson"+routelistArray[j].route,
        "paint": {
            "circle-radius": 4,
            "circle-opacity": 1,
            "circle-stroke-width": 3,
            "circle-stroke-color": "#f6c"
        }
        })

    };


    window.setInterval(function() {

        for(let j=0; j<routelistArray.length; j++) {
            var url = ('/api/v1/positions?period=now&rt='+routelistArray[j].route);
            map.getSource('vehicles_geojson'+routelistArray[j].route).setData(url);
            }
    }, 1000);

    // setup the viewport
    map.jumpTo({
        'center': [-74.0501, 40.7400],
        'zoom': 12
    });

    // ZOOM TO THE EXTENT
    // based on https://www.mapbox.com/mapbox-gl-js/example/zoomto-linestring/

    // todo zoom to extent of ALL lines (not just [n] in below)
    var coordinates = waypoints_geojson.data.features[3].geometry.coordinates;
    var bounds = coordinates.reduce(function(bounds, coord) {
      return bounds.extend(coord);
    }, new mapboxgl.LngLatBounds(coordinates[0], coordinates[0]));
    map.fitBounds(bounds, { padding: 20 });


});
