mapboxgl.accessToken = 'pk.eyJ1IjoiYml0c2FuZGF0b21zIiwiYSI6ImNqbDhvZnl1YjB4NHczcGxsbTF6bWRjMWQifQ.w2TI_q7ClI4JE5I7QU3hEA';
var map = new mapboxgl.Map({
    container: 'map',
    style: "mapbox://styles/mapbox/light-v9",
    center: [-74.50, 40], // starting position [lng, lat]
    zoom: 7 // starting zoom
});


// zoom implemented using https://stackoverflow.com/questions/49354133/turf-js-to-find-bounding-box-of-data-loaded-with-mapbox-gl-js

var url_vehicles = ("/api/v1/maps?layer=vehicles&rt=" + passed_route); // todo 1 make this worko on collections instead (can use the same script as busmap-colletions.js?


map.on('load', function() {


    $.getJSON(url_vehicles, (geojson) => {

        window.setInterval(function() {
            map.getSource('vehicles_source').setData(url_vehicles);
            }, 2000);


        map.addSource('vehicles_source', {
            type: 'geojson',
            data: geojson
        });
        map.fitBounds(turf.bbox(geojson), {padding: 20});

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
         },"stops") // layer to add before
        ;

    });

});

map.addControl(new mapboxgl.NavigationControl());

