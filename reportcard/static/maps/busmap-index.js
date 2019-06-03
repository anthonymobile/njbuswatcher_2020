mapboxgl.accessToken = 'pk.eyJ1IjoiYml0c2FuZGF0b21zIiwiYSI6ImNqbDhvZnl1YjB4NHczcGxsbTF6bWRjMWQifQ.w2TI_q7ClI4JE5I7QU3hEA';
var map = new mapboxgl.Map({
    container: 'map',
    style: "mapbox://styles/mapbox/light-v9"
    /*,
    center: [-74.50, 40], // starting position [lng, lat]
    zoom: 9 // starting zoom
    */
});


// from https://stackoverflow.com/questions/49354133/turf-js-to-find-bounding-box-of-data-loaded-with-mapbox-gl-js


var url_waypoints = ("/api/v1/maps?layer=waypoints&rt=all");

map.on('load', function() {

    $.getJSON(url_waypoints, (geojson) => {
        map.addSource('waypoints_source', {
            type: 'geojson',
            data: geojson
        });
        map.fitBounds(turf.bbox(geojson), {padding: 20});

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

    })
});

map.addControl(new mapboxgl.NavigationControl());

