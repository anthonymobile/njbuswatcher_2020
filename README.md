# Bus Rider Report Card 
### v 0.1 alpha
##### 15 August 2018


## Summary

This is set of scripts that fetch bus location and arrival prediction data from several API endpoints maintained by NJTransit (via vendor Clever Devices), synthesize and summarize this information, and present to riders in a number of useful ways via a simple, interactive web application. Implementation is in Python using pandas (data management and processing) and flask (web development). 

## Description

Users can explore our archive of arrival data for any stop on any route, fo a variety of pre-determined time periods. In the future, we plan to compute summary statistics and performance grades on the fly for each view. (e.g. "Route 119 for the stop at Webster Av and Congress St is currently performing at grade C+ for the week. That's down from a B last week.") 

### Filters/Views

The data gathered can be viewed along any combination of three criteria:
- Route: 87, 119 
- Stop: numbered stop from NJT database
- Period: history (all time - currently starts early August 2018), weekly, daily

### Current Metrics

V 0.1 provides a bare minimum of arrival information for any selected route, stop, and period

- Actual arrivals.
- Time between arrivals. 

### Future Metrics

- **Frequency of service.**  How often does a bus stop at my corner? This is simply calculated by looking at how often any in-service bus passes a given stop on a particular route. This will require additional period options (e.g. 'weekly-rush hours' or 'history-late nights') or an additional set of filters to confine the resampling to a relevant time period.
- **Bunching.** Related to frequency of service, we want to highlight any events when a bus arrives at a stop within 3 minutes or less than the previous service on the same route. (This is how the NYC MTA is currently defining bunching, according to [Streetsblog](https://nyc.streetsblog.org/2018/08/13/how-the-mta-plans-to-harness-new-technology-to-eliminate-bus-bunching/).
- **Travel time.** How long is it taking buses to get from one stop to the next? We can compare the arrival time of individual vehicles at successive stops along the line to identify which route segments are contributing the most to delays along the line at any given instant, and over time? This will require creating a data structure for route segments which doesn't currently exist (everything is organized around the stops themselves.) 
- **Schedule adherence.** Is the bus actually hitting its scheduled stops? This will require importing and looking up scheduled arrival times in GTFS timetables--initial inspection indicates this will be challenging (but not impossible) as run/service id numbers returned by the API don't seem to correspond to those listed in the GTFS data. How much we prioritize this will depend on community priorities--for rush hour service, it will be much less important; for late-night service, it will be crucial. Generally speaking, as more people use apps to monitor actual arrivals, schedule adherence is less of a pressing concern.
- **Performance Grade** (0-100, A+-F) Ideally, the app should present a letter or numerical grade summarizing performance for the current view to the user. Scaling and calibrating these will be challenging. We have not yet begun to even explore this.



### Look and Feel

This is an earlier wireframe -- v0.1 departs from this somewhat. (The OmniGraffle drawing is in the /ux folder of the repo.)

![the thing](doc/wireframe.png)


Here's a screenshot from the alpha release mid-August WIP.

![the thing](doc/screenshot-2018-08-15.png)

There's a lot of work to do of course., but its kind of amazing how fast you can stand up a data-driven app with flask, jinja, and bootstrap.

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
The basic theory here-since the NJTransit API doesn't provide a service to tell us when buses actually arrived at their stops--we instead constantly poll the arrival prediction endpointm once per minute, and take note of the last time we 'see' each bus about to reach the stop (e.g. the predicted arrival time is listed as "APPROACHING"). For instance, lets say we're pulling predicted arrivals for my corner stop on the 119, and our approach log looks like this:

- 8:32 am:  3min, 13min, 27min
- 8:33 am   APPROACHING, 12min, 25min
- 8:34 am   11min, 24min

What's happened is that the first bus pulled in, made its call, and departed between 8:33 and 8:34am. So we'll log it as arrival at 8:33am. 

This is a far from perfect method. But compare it to the absolutely [mind-blowing complexity of the tool](https://github.com/Bus-Data-NYC/inferno) that, for instance, the folks at Transit Center developed to interpolate stop calls using lat-lon positions, and you'll see that sometimes simple and consistent is probably better.

FWIW, we always deploy routewatcher.py alongside stopwatcher.py, so we are grabbing the lat, lon, route, and vehicle number to go back and audit the arrival estimates down the road, or plug-in a version of Transit Center's inferno tool. (<----pssst, grad students, two awesome thesis projects here.)


##### URLs

Here are the URLs currently exposed by the flask app.*

###### /nj/{route}/{stop}{period}/approaches
The raw underlying data, pulled from the arrival predictions API for the stop. We cron stopwatcher.py to record the predicted arrival time for each bus once per minute.

###### /nj/{route}/{stop}{period}/arrivals

List of actual "observed" arrival times. These are approximated by reviewing the appraoch log and recording the time of the last observed "APPROACHING" prediction for that vehicle as the time of arrival.

*n.b. the /nj in these routes. we are writing this to be source-agnostic, so they -should- work with any transit agency API provided by Clever Devices. Most of the documentation we used to figure out the API (which is uncodumented), came from the [unofficial guide to the Chicago CTA Bustracker API](https://github.com/harperreed/transitapi/wiki/Unofficial-Bustracker-API]) for instance.
