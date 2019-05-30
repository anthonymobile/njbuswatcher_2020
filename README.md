# NJ BusWatcher
v2.0
**30 may 2019**

---
# 23 DAYS TO FINISH

#### 
23 4-hour sprints

##### route headway test
    - accumulate some data on the desktop, need completed trips
    - **wwwAPI.RouteReport.get_headway** add {{headway}} tags to route.html template and start testing

##### route bunching write
    - **wwwAPI.RouteReport.get_bunching_badboys** write code and test
    
##### route bunching test
    - **wwwAPI.RouteReport.get_bunching_badboys** write code and test

##### route grade write and test
    - **wwwAPI.RouteReport.get_grade** write code and test

##### route page finalize layout
    - row 3
        - left = hourly table summarizing **Average Headway.** 
        - right = hourly table summarizing **Average Travel Time.**
        - borrow code from current `main` branch
    - row 4
        - buses on 'On the Road Now'
        - keep code in current template
        
##### stop page rough layout

    - row 1
        - left = grade card, 4 boxes
            - **qualitative grade** based on period: "SERVICE IS {good|fair|poor} {period}." --> "SERVICE IS GOOD
            - **frequency** Same as headway but labelled, presented a little differently.
            - **travel time** from here to the last stop for {period}
            - **travel speed** merge with one of the others, or separate box. a little bit of bling. average for last arrival over its most recent n stops?
            - **bunching** same as route
        - right = small map
    - row 2
        - hourly detail tables
        - left = **frequency/headway by hour** average for {period} 
        - right = **arrivals** with bunching highlights for {period}
        - borrow code from current `main` branch
        
##### stop travel time write
    - **wwwAPI.StopReport.get_travel_time** write code
##### stop travel time test
    - **wwwAPI.StopReport.get_travel_time** test 

##### stop travel time write
    - **wwwAPI.StopReport.get_travel_speed** write code

##### stop travel time test
    - **wwwAPI.StopReport.get_travel_speed** test 

##### stop grade write
    - **wwwAPI.StopReport.get_grade** write code

##### stop grade test
    - **wwwAPI.StopReport.get_grade** test 

##### stop arrivals dash write and test
    - **wwwAPI.StopReport.get_arrivals** write code and test 

##### stop frequency report write and test
    - **wwwAPI.StopReport.get_frequency_report** write code and test 

##### finalize home page
    - add a ranking somewhere of all the routes?  if you want to use this as an advocacy tool it may be useful to expose a ranking like that.
    - add the petition link to your footer next to CODE and API
    
##### route descriptions
    - **route_config.py**
        - complete descriptions for all lines
        - fix frequency for new lines
             
##### tripwatcher q.c. and optimization
    - error trapping for disconnected operation (dying now?)
    - `approach assignment`: 3+ position seems to still be having problems...
    - `Interpolate+log missed stops` after scanning each trip and logging any new arrivals, run a function that interpolates arrival times for any stops in between arrivals in the trip card -- theoretically there shouldn't be a lot though if the trip card is correct since we are grabbing positions every 30 seconds.
    - `Boomerang buses (Case E)`: any other indeterminate cases?
    
##### fix 404 page
    - replace old template with new base.html template

##### write static content
    - **about.html** 
    - **faq.html** 
    - **api.html** 
    
##### upload route images
    - add images for 2,6,10, 123, tk
     
##### maps zoom extent
    - busmap-index.js
        - add zoom to extent of vehicles_json layer
    - busmap-route.js
        - add zoom to extent of waypoints_json layer
    - busmap-stop.js
        - limit stop layer to single stop (w/ stops_json source set to '/api/v1/maps?layer=stops&rt=119&stop_id=30189') 
        - add zoom to extent of stops_json layer
     
##### review and test
    - check everything
    - log and fix bugs
    
##### deployment
    - check AWS time zones
    - reduce image size to fit on micro instance?
    - split tripwatcher, and / or map layers API into another instance to keep small+free


 
---
# BUSWATCHER

### Version 2

Improvements over v1
- rewritten in Python 3
- new localization and stop assignment algorithm is based on geographicposition and stop proximity not API arrival predictions
- full SQLalchemy database implementation for easier mix and match backend


### Overview

Buswatcher is a Python web app to collect bus position and stop arrival prediction data from several API endpoints maintained by NJTransit (via vendor Clever Devices), synthesize and summarize this information, and present to riders in a number of useful ways via a simple, interactive web application. Its implemented in Python using flask, pandas, and geopandas.

Check out a live version focusing on Jersey City  [buswatcher.code4jc.org](http://buswatcher.code4jc.org)

### Installation

It's all dockerized now. Use `docker-compose` and build from the project root.

#### Manual MySQL Database Creation

(for testing)

```
sudo mysql -u root -p
mysql> CREATE USER 'buswatcher'@'localhost' IDENTIFIED BY 'njtransit';
Query OK, 0 rows affected (0.00 sec)

mysql> GRANT ALL PRIVILEGES ON buses . * TO 'buswatcher'@'localhost';
Query OK, 0 rows affected (0.00 sec)

mysql> ALTER USER 'buswatcher'@'localhost' IDENTIFIED WITH mysql_native_password BY 'njtransit';
Query OK, 0 rows affected (0.00 sec)

mysql> flush privileges;
Query OK, 0 rows affected (0.00 sec)
```

### Components

- **tripwatcher.py**. Fetches bus current locations for a route from the NJT API, creates a `Trip` instance for each, and populates it with `ScheduledStop` instances for each stop on the service its running, and a `BusPosition` instance for each observed position.
- **reportcard.py** The flask app for routing incoming requests.
- **/lib** Core classes.
    - **DataBases.py**
        - *`Trip` Class*. The basis for all route performance metrics are Trips, represented in buswatcher by the `Trip` class. `Trip` instances are created by `tripwatcher.py` as needed to hold `BusPosition` instances (`BusPosition` is an inner class of `Trip`. `TripDB` instances handle writing to the database.
        
### API 

The API is a work in progress, but we will try to keep it robust and exposing all of the internal data used in the web app.

### endpoint: /api/v1/positions

We have a simple API set up with one endpoint for the bus positions data -- this is currently not used by the web app but will be once the new Localizer is done.

Usage with arguments
```
http://buswatcher.code4jc.org/api/v1/positions?rt=119&period=weekly
```

#### required arguments
`rt`    NJ transit route number (e.g. 119)
#### optional arguments
`period`  How much data to grab ('daily'=today, 'yesterday', 'weekly'=week to date,'history'=all time(default)) -- n.b. soon we'll add ability to query on specific dates in 'yyyy-mm-dd' format

`pd` Destination name (be careful will need an exact match)

`fs` Headsign display text

`dn` Compass direction of vehicle travel

`bid` Vehicle (e.g. bus) id, useful if you want to track a particular journey

`run` A specific scheduled trip (which ought to be but is not the GTFS trip_id which drives me bananas.) Actually better for tracking a journey, as you can compare between days and over periods even if the equipment changes.

`op` Probably operator(driver) id number.

`pid` Unknown purpose. But possibly a service identfier (e.g. direction or local/express or branch or some combination).

`dip` Unknown purpose.

`id` Unknown purpose.



#### response format

Reponses are geoJSON. Here's a typical record.
```
    {
      "geometry": {
        "coordinates": [
          -74.138438, 
          40.647728
        ], 
        "type": "Point"
      }, 
      "properties": {
        "bid": "8272", 
        "dip": "72242", 
        "dn": "SW", 
        "fs": "119 JERSEY CITY VIA CENTRAL BAYOONNE VIA JFK BLVD", 
        "id": "6053", 
        "op": "1031", 
        "pd": "Bayonne", 
        "pid": "1860", 
        "run": "916", 
        "timestamp": "Thu, 04 Oct 2018 20:10:01 GMT"
      }, 
      "type": "Feature"
    }, 

```

### endpoint: /api/v1/arrivals

This endpoint exposes the predictions about when buses running on a specific route will arrive at specific stops. This data is drawn off the NJT API and is the heart of how we currently log when buses call at stops. (This will be depreceated when the Localizer is done and we do it basedon actual observed bus locations.)

Usage with arguments
```
http://buswatcher.code4jc.org/api/v1/arrivals?rt=119&stop_id=30189&period=weekly
```

#### required arguments
`rt`    NJ transit route number (e.g. 119)

`stop_id`   NJ transit stop number (e.g. 30189)

#### optional arguments

Any of the fields in the JSON response below may be used as arguments. You'll get an error if you use an invalid query.

#### response format

Reponses are geoJSON. Here's a typical record.
```
    "{"pkey":28831,
    "pt":"APPROACHING",
    "rd":"87",
    "stop_id":"21062",
    "stop_name":"PALISADE AVE + SOUTH ST",
    "v":"5737",
    "timestamp":1540903024000,
    "delta":599000},
```


## External Resources

#### NJTransit API

Clever Devices API maintained by NJ Transit at http://mybusnow.njtransit.com/bustime/map/. For instance, here are all the buses on the #87, right now: [http://mybusnow.njtransit.com/bustime/map/getBusesForRoute.jsp?route=87](http://mybusnow.njtransit.com/bustime/map/getBusesForRoute.jsp?route=87)

#### Bus Metrics
Examples of transit agency and transit advocate bus metrics:
- [MBTA Back on Track](http://www.mbtabackontrack.com/performance/index.html#/detail/reliability/2018-12-01/Bus/Key%20Bus/1/)
- [BusTurnaround:Scorecards - Transit Center](http://busturnaround.nyc/#bus-report-cards)
- [NYC Bus Profile (BusStat.nyc)](http://www.busstat.nyc/methodology)

