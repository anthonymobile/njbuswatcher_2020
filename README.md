# NJ BusWatcher
v2.0
**14 feb 2019**

---
# ROADMAP TO COMPLETION

## NOW

**ALPHA_DEVELOPMENT**
- **route.html** 
    - wwwAPI.py - rebuild bunching_report / cron_nightly.py
    - middle section: Route Performance 
        -bunching grade
        -(see below -- mockup for now)  
- **wwwAPI**
    - StopReport.get_arrivals = continue debugging with a good bit of data
- **stop.html**
    - top
        - period picker bar
            - daily, monthly, history, specific date
    - hourly frequency
        - add a rough.js histogram / D3
    -  two column reports
        - left: arrivals for period w/ bunched arrivals highlighted
        - right: hourly frequency for period
            - make a histogram using the rough.js bar chart (embed script in page if its easier)        
- **about.html** 
    - write content
- **index.html**
    - map = fix starting extent (zoom to extent of ALL lines, not just the arbitrary nth [n] line in the route array as currently)
    - add breadcrumb separators

- **route_config.py**
    - short and long descriptions for the new lines


## MUST DO BEFORE LAUNCH

**PRE_DEPLOYMENT** 
- docker (build with`docker-compose up -d --build`)
    1. finish builds
        - nginx
            - working good
            - serves up static files
        - flask-gunicorn
            - running ok, why doesnt nginx connect?
            - try putting gunicorn command back in docker-compose.yml or a better way of running than CMD in Dockerfile? (supervisor?)
    2. add postgres integration
        - **DataBases.py**
            - change data store to postgres
    3. `deploy to AWS free micro instance`

**tripwatcher.py**
- `approach assignment`: 3+ position seems to still be having problems...
-`simplify/comment out console logging`:   
    - make clearer that only displaying stops that dont have approach logged yet
    - fix the approach array for 1-position	approaches to be consistent
		 0.0,195 distance_to_stop 195
     - remove other extraneous output
- `Interpolate+log missed stops` after scanning each trip and logging any new arrivals, run a function that interpolates arrival times for any stops in between arrivals in the trip card -- theoretically there shouldn't be a lot though if the trip card is correct since we are grabbing positions every 30 seconds.
- `Boomerang buses (Case E)`: Bus that gets assigned to a stop it already visited after doubling back on a parallel street -- e.g. the 87 going down the hill getting localized to Palisade Ave stops again.

## FUTURE

**NEW METRICS !!! WHY I STARTED THE WHOLE DAMN REFACTOR !!**

**Localizer.py**
- `More accurate distance conversion`:  at least verify how far off we are. current method is using a crude assumption (1 degree = 69 miles = 364,320 feet). more accurate method - "If CRS of geodfs are EPSG 4326 (lat/lon) then returned 'dist' will be in degrees. To meters or ft either first convert both gdf to appropriate CRS proj for your location using .to_crs() or convert from degrees [link](https://t.co/FODrAWskNH)".

**templates/trip_dash.html** 
- `Approach plotter`: Plot every?/current approach to the dash.

**Databases.py** 
- `relationships! use them!` `children_ScheduledStops` and `parent_Trip` are incredibly use attributes any record i pull from the db will have now. use them to extend the query sets we get back!!!!
- `Exception handler`: smarter check in get_session on table creation --> try if table exists == False:

---
# MAIN DOCUMENTATION



### Version 2

Improvements
- rewritten in Python 3
- new localization and stop assignment algorithm is based on geographicposition and stop proximity not API arrival predictions
- full SQLalchemy database implementation for easier mix and match backend


### /reportcard

#### tripwatcher.py
The main background process, cron on a 30-second 

### /reportcard/lib

#### Localizer	


#### A1. Route Performance Metrics

##### Reference
Examples of transit agency and transit advocate bus metrics:
- [MBTA Back on Track](http://www.mbtabackontrack.com/performance/index.html#/detail/reliability/2018-12-01/Bus/Key%20Bus/1/)
- [BusTurnaround:Scorecards - Transit Center](http://busturnaround.nyc/#bus-report-cards)
- [NYC Bus Profile (BusStat.nyc)](http://www.busstat.nyc/methodology)


##### Data Basis: Trip Class

**Description.**
The basis for all route performance metrics are Trips, represented in buswatcher by the `Trip` class. `Trip` instances are created by `tripwatcher.py` as needed to hold `BusPosition` instances (`BusPosition` is an inner class of `Trip`. `TripDB` instances handle writing to the database.

**Data Acquisition.** `tripwatcher.py` fetches bus current locations for a route from the NJT API, creates a `Trip` instance for each, and populates it with a `BusPosition` instance for each observed position. `TripDB` is called to write to the database, creating a table for that route (e.g. `triplog_87`). Since timestamps will always be different, no checks are made for duplicates. Each record is stamped with a unique trip identifier `(v,run,date)` (where date=YYYY-MM-DD) combination, e.g. `4356_305_20181004`.

**Average Headway.** This provides a way of capturing the bunching in a single, easily understood metric. We can also report variability using standard deviation and that can be converted to a letter grade (e.g. A is < 1 s.d., B is 1 to 1.5, etc.) Example:

```Route 87 has an average headway of 20 minutes, with a service dependability grade of B. That means 80 percent of the time the bus will come every 10 to 30 minutes.``` (This needs wordsmithing!)

*Implementation.*
For all completed trips in `{period}`, sampling every n minutes, what is the average travel time interval between buses along the route? 

- *Using Old Localizer:* Calculate by looking at the last two arrivals for every stop and using that as the average headway at that stop for that sample point, average over all the measurements.

- *Using New Localizer:* Calculate the on-the-road-Directions-API travel time between each two buses in the Trip and average over all the measurements.
    

**Average Travel Time.** This indicates how long it takes, on average for all observed runs over the `{period}`, to travel from STOP A to STOP B.

- On ROUTE VIEW, user chooses the two stops from 'Travel Time Report' drop downs.
- Algorithm
    - SELECT all calls at the two stops in the period in question from `routelog_87`
    - create `Trip` instances for each unique (v,run,date) and calculate travel time between the two stops (set in property `Trip.travel_time_a_to_b` or some such)
    - average over the entire group
   
**Average Travel Speed.** Calculate over entire route. If there are trouble spots, in the future, we can calculate this at every observed position with New Localizer. 


#### A2. Stop Performance Metrics

- as letter grade and description, or
- as literal: e.g. 'TODAY IS TYPICAL. TODAY IS WORSE THAN USUAL.'
- stop level metrics: - stop.html: THIS STATION USUALLY HAS DECENT SERVICE or THIS STATION HAS GOOD SERVICE TODAY or something like that.
- stop report page: add additional period options
    - rush hours (as a toggle?)
    - weekdays (as a toggle?)
    - owl (as a toggle?)
    - date picker
    - date range picker
    - others?
   

### C. Charts and Maps
Implement with Chart.js
1. bus frequency symbol histogram (STOP report)
    - histogram showing how many buses arrived at stop during each 30 minute bin
    - modeled after [Nobel prize D3 viz](https://github.com/Kyrand/dataviz-with-python-and-js/tree/master/nobel_viz_D3_V4) from Python+JS book
        - implementation: concatenate the 3 nobel scripts (core,main,time)
        - 30 minute bins
    - optional: show all buses on all routes arriving, each route different color? (would require add/rewrite lib.StopReport) 
2. ridership dataviz
    - get from NJT or APTA
    
3. Map Improvements
    - Show Congestion
        - change color of bunching buses on the map? 
        - indicate congested route segments   

        


    
# Other TODOs  

#### A. Caching Framework

Install and update docs for redis caching backend for easycache framework. Currently have to install all of django just to use its caching framework.
    - First, install redis server per [redis-py package docs](https://pypi.org/project/redis/)
    - Second, instantiate the cache:

    ```python
        from redis import StrictRedis
        from easy_cache.contrib.redis_cache import RedisCacheInstance
        from easy_cache import caches
        
        redis_cache = RedisCacheInstance(StrictRedis(host='...', port='...'))
        caches.set_default(redis_cache)
        
        # will use `default` alias
        @ecached(...)

    ```

#### B. Import Old Data
- in 'buses_summer2018' database
- in 'buses_fall018' database


#### C. Setup DB Backup Slave 
- [howto](https://www.digitalocean.com/community/tutorials/how-to-move-a-mysql-data-directory-to-a-new-location-on-ubuntu-16-04)

# Misc Ideas

#### Trip Playback
Generate a list of runs, linked to 'playback' pages via an API call that spits out geojson for all points in routelog for a single run, on a specific date, and display on a page using mapbox live update [tutorial](https://www.mapbox.com/mapbox-gl-js/example/live-update-feature/).

#### New Services data structure  
Currently the way we model services is very bad, because the NJT API only exposes route metadata for services currently running. There are two ways we could build up a more universal model. 
1. From GTFS. Would require overcoming the considerable challenges of mapping the Clever Devices codes to GTFS (not sure they are the same, maybe we can FOIL this)
2. Build it up from the API over time
    - Create a class for services, with tables in db
    - These get populated as the lines are loaded
    - Grabbers and webpages are smart and don't die if they try to grab a service that's not active
    - Hardcode the headsigns if they are ambigious 
    
#### GTFS Integration
This is a big deal but a major headache. Working with GTFS in [Jupyter](http://simplistic.me/playing-with-gtfs.html).
What's needed: 
- module to create lookup table GTFS:Clever_Devices - timestamp_hr_min+run_id --> gtfs: trip_id+start_time so we can match routelog.run to gtfs.trip_id
- GTFS integration:  write a routine to match gtfs trip_id, start_time :: timestamp,run for first observation of a v in routelog series (e.g. map run to trip_id) -- either a machine learning model or something simpler 
    
---

# Overview

Buswatcher is a set of Python scripts and web apps to collect bus position and stop arrival prediction data from several API endpoints maintained by NJTransit (via vendor Clever Devices), synthesize and summarize this information, and present to riders in a number of useful ways via a simple, interactive web application. Its implemented in Python using flask, pandas, geopandas, shapely, and easy_cache


### Demo

Check out a live version focusing on Jersey City Heights [buswatcher.code4jc.org](http://buswatcher.code4jc.org)

The app is more of less skinnable for any NJ community with a minimum of re-configuration:
- route_config.py - holds all route numbers and descriptions
- cron jobs (need to setup stopwatcher.py and routewatcher.py for each route tracked)

### Key Metrics
The data supports a number of rider and service provider metrics that are in various stages of being implemented.

- **Frequency of service.** (working). How often does a bus stop at my corner? Calculated by looking at how often any in-service bus passes a given stop on a particular route.
- **Bunching.** (working) Related to frequency of service, we want to highlight any events when a bus arrives at a stop within 3 minutes or less than the previous service on the same route. (This is how the NYC MTA is currently defining bunching, according to [Streetsblog](https://nyc.streetsblog.org/2018/08/13/how-the-mta-plans-to-harness-new-technology-to-eliminate-bus-bunching/).
- **Travel time.** (future) How long is it taking buses to get from one stop to the next? We can compare the arrival time of individual vehicles at successive stops along the line to identify which route segments are contributing the most to delays along the line at any given instant, and over time? This will require creating a data structure for route segments which doesn't currently exist (everything is organized around the stops themselves.) 
- **Schedule adherence.** (future) Is the bus actually hitting its scheduled stops? This will require importing and looking up scheduled arrival times in GTFS timetables--initial inspection indicates this will be challenging (but not impossible) as run/service id numbers returned by the API don't seem to correspond to those listed in the GTFS data. How much we prioritize this will depend on community priorities--for rush hour service, it will be much less important; for late-night service, it will be crucial. Generally speaking, as more people use apps to monitor actual arrivals, schedule adherence is less of a pressing concern.
- **Performance Grade** (future)  Ideally, the app should present a letter or numerical grade summarizing performance for the current view to the user (e.g. 0-100, A+-F).



## API 

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


## Implementation Details

Written in python as a set of cron-able scripts that pull data once per minute from the Clever Devices API maintained by NJ Transit at http://mybusnow.njtransit.com/bustime/map/. For instance, here are all the buses on the #87, right now: [http://mybusnow.njtransit.com/bustime/map/getBusesForRoute.jsp?route=87](http://mybusnow.njtransit.com/bustime/map/getBusesForRoute.jsp?route=87)

Here's what does what.

### systemwatcher.py
This is a somewhat aggressive grabber that sucks down the entire statewide position report. We don't actually use it, but its provided as the basis from which everything else was derived. Written by Alex Reynolds -- the amazingly efficient object and data structure Alex created here has made the whole project more robust and efficient, as most of the other classes either directly inherit or are otherwise derived from the ones here.

### routewatcher.py 
Pulls only position reports for buses currently running on a single, specific route.

### stopwatcher.py
Pulls arrival predictions from one API call for buses inbound to a specific stop. We iterate over all stops in a route using another API call that pumps out the route points.

### report_card.py
Flask app which renders the report cards for various routes and views.

## How It All Works

Most of the heavy lifting is done by lib/ReportCard.py. The basic theory here-since the NJTransit API doesn't provide a service to tell us when buses actually arrived at their stops--we instead constantly poll the arrival prediction endpointm once per minute, and take note of the last time we 'see' each bus about to reach the stop (e.g. the predicted arrival time is listed as "APPROACHING"). For instance, lets say we're pulling predicted arrivals for my corner stop on the 119, and our approach log looks like this:

- 8:32 am:  3min, 13min, 27min
- 8:33 am   APPROACHING, 12min, 25min
- 8:34 am   11min, 24min

What's happened is that the first bus pulled in, made its call, and departed between 8:33 and 8:34am. So we'll log it as arrival at 8:33am. 

This is a far from perfect method. But compare it to the absolutely [mind-blowing complexity of the tool](https://github.com/Bus-Data-NYC/inferno) that, for instance, the folks at Transit Center developed to interpolate stop calls using lat-lon positions, and you'll see that sometimes simple and consistent is probably better.

FWIW, we always deploy routewatcher.py alongside stopwatcher.py, so we are grabbing the lat, lon, route, and vehicle number to go back and audit the arrival estimates down the road, or plug-in a version of Transit Center's inferno tool. (<----pssst, grad students, two awesome thesis projects here.)


##### URLs

Here are the URLs currently exposed by the flask app.*

###### /nj/{route}
A basic route reportcard -- shows a map (currently just a jpg we stole from Moovit), a list of the top 10 stops based on how many times buses have arrived bunched there today. At the bottom is a clickable list of all currently running services and all the stops on those services. The stops go to the stop report pages (next).


###### /nj/{route}/stop/{stop}/{period}

A basic stop reportcard -- shows an arrival history with route (just for diagnostics now we had some issues with stragglers coming up from other routes at the same stop and still trying to debug it), time, bus id, and the interval from last arrival. Red indicates that bus showed up 'bunched', 3 mins or less than the previous arrival. on the right is a summary of the average time between buses per hour -- everything updates for whatever period you chooce from the breadcrumb menu at the top.



*n.b. the /nj in these routes. we are writing this to be source-agnostic, so they -should- work with any transit agency API provided by Clever Devices. Most of the documentation we used to figure out the API (which is uncodumented), came from the [unofficial guide to the Chicago CTA Bustracker API](https://github.com/harperreed/transitapi/wiki/Unofficial-Bustracker-API]) for instance.

## External Resources

#### Transit Center Bus Turnaround
Particularly the [district-level report cards](http://districts.busturnaround.nyc/). There's also some useful service metric definitions there that we may borrow in the future.

>Bunching data are calculated as an average of performance during weekdays between the hours of 10am-4pm, for the months of May and October 2017. These two months are selected because they contain minimal holidays, mild weather (minimizing service disruptions), and fall during the school year.

>Bunching is defined as the percentage of buses that arrive at less than 25 percent of the scheduled interval behind the previous bus. So if Bus #2 is scheduled to arrive eight minutes after Bus #1, but instead Bus #2 arrives less than two minutes after Bus #1, then Bus #2 is considered "bunched". Bus arrival and departure times are estimated using an algorithm developed by Nathan Johnson and Neil Freeman, and applied to the MTA's Bus Time data. More information about Bus Time data is available here.

> Speed is calculated using the same Bus Time data in conjunction with route length information gathered from the MTA's publicly provided GTFS schedules. As presented here at the route level, the travel time from start to finish is simply divided by the route's length to calculate average speed. More details available in the performance API documentation.

## Installation

It's all dockerized now. Fire up an AWS or Digital Ocean instance and try it out. Instructions to come.