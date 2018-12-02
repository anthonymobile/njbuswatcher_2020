
/*------------------------------

USING FUNCTION CHAINING
for easier reading

------------------------------ */
route='87';

function logResult(result) {
  console.log(result);
}

function logError(error) {
  console.log('Looks like there was a problem: \n', error);
}

function validateResponse(response) {
  if (!response.ok) {
    throw Error(response.statusText);
  }
  return response;
}

function readResponseAsXML(response) {
  let responseDoc = new DOMParser().parseFromString(response, 'application/xml');
  var oSerializer = new XMLSerializer();
  var buses_xml = oSerializer.serializeToString(responseDoc);
  return buses_xml;
}


jQuery.ajaxPrefilter(function(options) {
    if (options.crossDomain && jQuery.support.cors) {
        options.url = 'https://cors-anywhere.herokuapp.com/' + options.url;
    }
});

//--------- CORS SNIPPET

(function() {
    var cors_api_host = 'stormy-earth-44085.herokuapp.comm';
    var cors_api_url = 'https://' + cors_api_host + '/';
    var slice = [].slice;
    var origin = window.location.protocol + '//' + window.location.host;
    var open = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function() {
        var args = slice.call(arguments);
        var targetOrigin = /^https?:\/\/([^\/]+)/i.exec(args[1]);
        if (targetOrigin && targetOrigin[0].toLowerCase() !== origin &&
            targetOrigin[1] !== cors_api_host) {
            args[1] = cors_api_url + args[1];
        }
        return open.apply(this, args);
    };
})();

//--------- CORS SNIPPET




function fetchXML(pathToResource) {
  fetch(pathToResource,{mode:'origin'} ) // 1
  .then(validateResponse) // 2
  .then(readResponseAsXML) // 3
  // then convertResponseToJSON 3a
  // then convertJSONtoGeoJSON 3b
  .then(logResult) // 4
  .catch(logError);
}

fetchXML('https://stormy-earth-44085.herokuapp.com/http://mybusnow.njtransit.com/bustime/map/getRoutePoints.jsp?route='+ route);
