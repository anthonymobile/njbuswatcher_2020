# Rider Report Card 
##### 5 July 2018 Update

n.b. Not a working release -- see below for what's working and is still WIP

### A Report Card for NJ Transit Bbuses

We are building a website that will provide line-by-line and stop-by-stop report cards for on-time performance across the New Jersey Transit bus system using real-time and archived data collected from the system's own online services. 

This is a sketch of what we want to deliver work in progress. (The OmniGraffle drawing is in the /ux folder of the repo.)

![the thing](doc/wireframe.png)


There are 3 separate sets of data that can be used to calculate scores that inform riders and hold NJT accountable.

1. Frequency of service. How often does a bus stop at my corner? This is simply calculated by looking at how often any in-service bus passes a given stop on a particular route.
2. Travel time. How long is it taking buses to get from one stop to the next. What segments are contributing the most to delays along the line at any given instant, and over time?
3. Schedule adherence. Is the bus actually hitting its scheduled stops? This is more of an issue on less frequent routes, and its becoming less important as more people use apps to meet the bus. At rush time its often not at all important. But its pretty easy to do, comparing against GTFS timetables, so lets do it.

Not sure yet whether to report this kind of detail (as seen above), how to summarize it -- e.g. as a single score, a letter, etc.


## Implementation

Written in python as a set of cron-able scripts that pull data once per minute from the Clever Devices API maintained by NJ Transit at http://mybusnow.njtransit.com/bustime/map/. For instance, here are all the buses on the #87, right now: [http://mybusnow.njtransit.com/bustime/map/getBusesForRoute.jsp?route=87](http://mybusnow.njtransit.com/bustime/map/getBusesForRoute.jsp?route=87)

### systemwatcher.py (works)
This is a somewhat aggressive grabber that sucks down the entire statewide position report. We don't actually use it, but its provided as the basis from which everything else was derived. Written by Alex Reynolds.

### routewatcher.py (WIP)
Pulls only position reports for buses currently running on a single, specific route.

### stopwatcher.py (works)
Pulls arrival predictions from one API call for buses inbound to a specific stop. We iterate over all stops in a route using another API call that pumps out the route points.

### arrival_spotter.py (WIP)
Does a lot of stuff to figure out when buses actually make the call at the stop.

### report_card.py (WIP)
Flask app which renders the report cards for various routes and views.

