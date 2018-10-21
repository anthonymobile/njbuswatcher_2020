// Map via Mapbox GL

$(document).ready(init);

function init(jQuery) {
  CurrentYear();
  initMap();

  /*
  // user clicks some button
  $('#someButton').on('click', function () {
      // do something here
  });

  */
}

function CurrentYear() {
  var thisYear = new Date().getFullYear()
  $("#currentYear").text(thisYear);
}

var mapCoordinates = [40.7400,-74.0501];
var mapZoom = 13;

// buswatcher MapBox key (anthony@bitsandatoms.net)
var mapAccessToken = "pk.eyJ1IjoiYml0c2FuZGF0b21zIiwiYSI6ImNqbDhvZnl1YjB4NHczcGxsbTF6bWRjMWQifQ.w2TI_q7ClI4JE5I7QU3hEA";

var map = null;
var geocoder = null;

function initMap() {
  map = MapGL();
}

function MapGL() {
  mapboxgl.accessToken = mapAccessToken;

  // initialize map
  var newMap = new mapboxgl.Map({
      container: "map", // container id
      style: "mapbox://styles/mapbox/light-v9", //stylesheet location
      center: [-74.0501, 40.7400], // starting position
      zoom: 13 // starting zoom
  });

    newMap.addLayer({
            'id': 'daily',
            'type': 'symbol',
            'source': {
                        'type': 'geojson',
                        'data': 'http://buswatcher.code4jc.org/api/v1/positions/?rt=119&period=daily'
                },
             'layout': {
                        'icon-image': '{icon}-15'
                        }
                  }
            );
  
  // event handlers
  newMap.on("load", mapLoaded);
    return newMap;
}

function mapLoaded() {
  // do stuff here
  
}