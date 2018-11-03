// grabs JSON via AJAX from API

var API_URL='http://localhost:5000/api/v1/arrivals';

var displayJSON = function(query) {

    d3.json(API_URL + query, function (error, data) {

        // log any error to console
        if(error){
            return console.warn(error);
        }

        d3.select('#query pre').html(query);
        d3.select('#data pre').html(JSON.stringify(data, null, 4).replace(/\\"/g, '"'));
        console.log(data);
    });
};

var query = '?rt=87&stop_id=21062&period=weekly';

displayJSON(query);