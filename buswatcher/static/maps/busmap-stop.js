// see if possible to collapse into busmap-index.js -- perhaps just pass a var view_type (index, collection, route, stop) and then use conditionals to control display of layers
// might need to be different since we want a single stop - limit stop layer to single stop (w/ stops_json source set to '/api/v1/maps?layer=stops&rt=119&stop_id=30189') - to extent of stops_json layer


mapboxgl.accessToken = 'pk.eyJ1IjoiYml0c2FuZGF0b21zIiwiYSI6ImNqbDhvZnl1YjB4NHczcGxsbTF6bWRjMWQifQ.w2TI_q7ClI4JE5I7QU3hEA';
var map = new mapboxgl.Map({
    container: 'map',
    style: "mapbox://styles/mapbox/light-v9",
    zoom: 0
});


map.on('load', function() {

    // setup the viewport
    map.jumpTo({
        'center': [-74.0501, 40.7400],
        'zoom': 16
    });


    // ROUTES
    var url_waypoints = ("/api/v1/maps?layer=waypoints&rt="+passed_route);
    map.addSource('waypoints_geojson', {
        "type": "geojson",
        "data": url_waypoints
    });
    map.addLayer({
        "id": "route",
        "type": "line",
        "source": "waypoints_geojson",
        "paint": {
            "line-color": "blue",
            "line-opacity": 0.75,
            "line-width": 3
        }
    });

    // STOPS
    var url_stops = ("/api/v1/maps?layer=stops&rt="+passed_route+"&stop="+passed_stop_id);
    map.addSource('stops_geojson', {
        "type": "geojson",
        "data": url_stops
    });
    map.addLayer({
        "id": "stops",
        "type": "circle",
        "source": "stops_geojson",
        "paint": {
            "circle-radius": 2,
            "circle-opacity": 1,
            "circle-stroke-width": 2,
            "circle-stroke-color": "#fff"
        }
    });


    // VEHICLES


    var url_vehicles = ("/api/v1/maps?layer=vehicles&rt="+passed_route);
    map.addSource('vehicles_geojson', {
        "type": "geojson",
        "data": url_vehicles
    });
    map.addLayer({
        "id": "vehicles",
        "type": "circle",
        "source": "vehicles_geojson",
        "paint": {
            "circle-radius": 4,
            "circle-opacity": 1,
            "circle-stroke-width": 3,
            "circle-stroke-color": "#f6c"
        }

    });

    window.setInterval(function() {
        map.getSource('vehicles_geojson').setData(url_vehicles);
    }, 1000);



});
