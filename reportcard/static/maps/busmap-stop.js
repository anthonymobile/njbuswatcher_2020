mapboxgl.accessToken = 'pk.eyJ1IjoiYml0c2FuZGF0b21zIiwiYSI6ImNqbDhvZnl1YjB4NHczcGxsbTF6bWRjMWQifQ.w2TI_q7ClI4JE5I7QU3hEA';
var map = new mapboxgl.Map({
    container: 'map',
    style: "mapbox://styles/mapbox/light-v9",
    zoom: 0
});


map.on('load', function() {

    // starting view
    // var mapCoordinates = [passed_stop_coordinates];
    // var mapZoom = 15;


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

    // STOP
    var stop_geojson = {
        type: 'geojson',
        data: passed_stop_geojson
    };

    map.addSource('stop_geojson', stop_geojson);

    map.addLayer({
        "id": "stop",
        "type": "circle",
        "source": "stop_geojson",
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
    }, 5000);

    // setup the viewport
    map.jumpTo({
        'center': [passed_stop_coordinates],
        'zoom': 15
    });


    // HOVER TOOLTIPS

    for(let j=0; j<routelistArray.length; j++) {


        var popup = new mapboxgl.Popup({
            closeButton: false,
            closeOnClick: false
        });

        map.on('mouseenter', ('vehicles'+routelistArray[j].route), function(e) {
            // Change the cursor style as a UI indicator.
            map.getCanvas().style.cursor = 'pointer';

            var coordinates = e.features[0].geometry.coordinates.slice();
            var description = (e.features[0].properties.fs + ", Bus " + e.features[0].properties.id + ", Driver " + e.features[0].properties.op + ", Run " + e.features[0].properties.run);

            // Ensure that if the map is zoomed out such that multiple
            // copies of the feature are visible, the popup appears
            // over the copy being pointed to.
            while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
                coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360;
            }

            // Populate the popup and set its coordinates
            // based on the feature found.
            popup.setLngLat(coordinates)
                .setHTML(description)
                .addTo(map);
        });

        map.on('mouseleave', ('vehicles'+routelistArray[j].route), function() {
            map.getCanvas().style.cursor = '';
            popup.remove();
        });

    }




});
