// 1. get the xml from NJT API for a single route

var route = '87';

let url = ('http://mybusnow.njtransit.com/bustime/map/getRoutePoints.jsp?route='+ route)
let request = new Request(url);

fetch(request,{mode: 'no-cors'}).then((results) => {
  // results returns XML. lets cast this to a string, then create
  // a new DOM object out of it!
  results
	.text()
	.then(( str ) => {
	  let responseDoc = new DOMParser().parseFromString(str, 'application/xml');

	  var oSerializer = new XMLSerializer();
	  var buses_xml = oSerializer.serializeToString(responseDoc);

	  // TURN IT INTO JSON

	  // Create the return object
	  var obj = {};

	  if (buses_xml.nodeType == 1) { // element
			// do attributes
			if (buses_xml.attributes.length > 0) {
			obj["@attributes"] = {};
				for (var j = 0; j < xml.attributes.length; j++) {
					var attribute = xml.attributes.item(j);
					obj["@attributes"][attribute.nodeName] = attribute.nodeValue;
				}
			}
		} else if (buses_xml.nodeType == 3) { // text
			obj = buses_xml.nodeValue;
		}

		// do children
		if (buses_xml.hasChildNodes()) {
			for(var i = 0; i < buses_xml.childNodes.length; i++) {
				var item = buses_xml.childNodes.item(i);
				var nodeName = item.nodeName;
				if (typeof(obj[nodeName]) == "undefined") {
					obj[nodeName] = xmlToJson(item);
				} else {
					if (typeof(obj[nodeName].push) == "undefined") {
						var old = obj[nodeName];
						obj[nodeName] = [];
						obj[nodeName].push(old);
					}
					obj[nodeName].push(xmlToJson(item));
				}
			}
		}
		return obj;
	})

});



// 3. rewrite as geojson
    // for bus in json, rewrite a record
