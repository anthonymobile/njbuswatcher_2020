mapboxgl.accessToken = 'pk.eyJ1IjoiYml0c2FuZGF0b21zIiwiYSI6ImNqbDhvZnl1YjB4NHczcGxsbTF6bWRjMWQifQ.w2TI_q7ClI4JE5I7QU3hEA';
var map = new mapboxgl.Map({
    container: 'map',
    style: "mapbox://styles/mapbox/light-v9",
    zoom: 0
});


map.on('load', function() {

    // setup the viewport
    map.jumpTo({
        'center': [-74.2501, 40.0000],
        'zoom': 7
    });


    // ROUTES
    var url_waypoints = ("/api/v1/maps?layer=waypoints&rt=all");
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
    var url_stops = ("/api/v1/maps?layer=stops&rt=all");
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


    var url_vehicles = ("/api/v1/maps?layer=vehicles&rt=all");
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
