mapboxgl.accessToken = 'pk.eyJ1IjoiYml0c2FuZGF0b21zIiwiYSI6ImNqbDhvZnl1YjB4NHczcGxsbTF6bWRjMWQifQ.w2TI_q7ClI4JE5I7QU3hEA';
var map = new mapboxgl.Map({
    container: 'map',
    style: "mapbox://styles/mapbox/light-v9",
    zoom: 0
});


map.on('load', function() {

    // setup the viewport
    map.jumpTo({
        'center': [-74.5, 40.15],
        'zoom': 7
    });


    // https://stackoverflow.com/questions/2177548/load-json-into-variable


    ////////////////////////////
    // WAYPOINTS
    ////////////////////////////

    // ajax request for waypoints data
    var url_waypoints = ("/api/v1/maps?layer=waypoints&rt=all");
    var waypoints_geojson = (function () {
        var json = null;
        $.ajax({
            'async': false,
            'global': false,
            'url': url_waypoints,
            'dataType': "json",
            'success': function (data) {
                json = data;
            }
        });
        return json;
    })();

    // add waypoints to map
    map.addSource('waypoints_source', {
    "type": "geojson",
    "data": waypoints_geojson
        });

    map.addLayer({
        "id": "route",
        "type": "line",
        "source": "waypoints_source",
        "paint": {
            "line-color": "blue",
            "line-opacity": 0.75,
            "line-width": 3
        }
    });

    ////////////////////////////
    // STOPS
    ////////////////////////////

    // ajax request for stops data
    var url_stops = ("/api/v1/maps?layer=stops&rt=all");
    var stops_geojson = (function () {
        var json = null;
        $.ajax({
            'async': false,
            'global': false,
            'url': url_stops,
            'dataType': "json",
            'success': function (data) {
                json = data;
            }
        });
        return json;
    })();

    // add stops to map
    map.addSource('stops_source', {
    "type": "geojson",
    "data": stops_geojson
        });

    map.addLayer({
        "id": "stops",
        "type": "circle",
        "source": "stops_source",
        "paint": {
            "circle-radius": 2,
            "circle-opacity": 1,
            "circle-stroke-width": 2,
            "circle-stroke-color": "#fff"
        }
    });


    ////////////////////////////
    // VEHICLES
    ////////////////////////////

    // ajax request for vehicles data
    var url_vehicles = ("/api/v1/maps?layer=vehicles&rt=all");
    var vehicles_geojson = (function () {
        var json = null;
        $.ajax({
            'async': false,
            'global': false,
            'url': url_vehicles,
            'dataType': "json",
            'success': function (data) {
                json = data;
            }
        });
        return json;
    })();

    // add vehicles to map
    map.addSource('vehicles_source', {
    "type": "geojson",
    "data": vehicles_geojson
        });

    map.addLayer({
        "id": "vehicles",
        "type": "circle",
        "source": "vehicles_source",
        "paint": {
            "circle-radius": 4,
            "circle-opacity": 1,
            "circle-stroke-width": 3,
            "circle-stroke-color": "#f6c"
        }
     })
    ;



/*
    ////////////////////////////
    // ZOOM CODE
    ////////////////////////////

    // from https://www.isaveutime.com/mapbox-fitbounds-using-geojson/
    // // Run once the vehicles data request is complete
    // $.when(vehicles_geojson).done(function () {

    // from https://docs.mapbox.com/mapbox-gl-js/example/zoomto-linestring/
    var coordinates = waypoints_geojson.features[0].geometry.coordinates;
    // todo make bounds zoom to ALL lines
    var bounds = coordinates.reduce(function(bounds, coord) {
    return bounds.extend(coord);
    }, new mapboxgl.LngLatBounds(coordinates[0], coordinates[0]));

    map.fitBounds(bounds, {
    padding: 20
    });
*/


    ////////////////////////////
    // ZOOM CODE - BETTER
    ////////////////////////////

    // https://stackoverflow.com/questions/35586360/mapbox-gl-js-getbounds-fitbounds

    var bounds = new mapboxgl.LngLatBounds();
    waypoints_geojson.features.forEach(function(feature) {
        bounds.extend(feature.geometry.coordinates);
    });

    map.fitBounds(bounds, { padding: '20' });


});


