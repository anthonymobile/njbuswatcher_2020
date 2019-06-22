mapboxgl.accessToken = 'pk.eyJ1IjoiYml0c2FuZGF0b21zIiwiYSI6ImNqbDhvZnl1YjB4NHczcGxsbTF6bWRjMWQifQ.w2TI_q7ClI4JE5I7QU3hEA';
var map = new mapboxgl.Map({
    container: 'map',
    style: "mapbox://styles/mapbox/light-v9",
    center: [-74.50, 40], // starting position [lng, lat]
    zoom: 7 // starting zoom
});

var url_waypoints = ("/api/v1/maps?layer=waypoints&rt="+passed_route); /* todo 0 test and fix as needed */
var url_vehicles = ("/api/v1/maps?layer=vehicles&rt="+passed_route); /* todo 0 test and fix as needed */

map.on('load', function() {


    $.getJSON(url_vehicles, (geojson) => {
        map.addSource('vehicles_source', {
            type: 'geojson',
            data: geojson
        });
        /* map.fitBounds(turf.bbox(geojson), {padding: 20}); */

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

    });

        $.getJSON(url_waypoints, (geojson) => {
        map.addSource('waypoints_source', {
            type: 'geojson',
            data: geojson
        });
        map.fitBounds(turf.bbox(geojson), {padding: 50});

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
    });

        window.setInterval(function() {
        map.getSource('vehicles_source').setData(url_vehicles);
        }, 5000)

});


map.addControl(new mapboxgl.NavigationControl());

