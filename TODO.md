updated 8 nov 2018

#### development branch to-do
1. new page off route report for bunching report
2. fix caching for bunching_report (doesnt work?)
3. bug: just after midnight: when there are no arrivals, stops page returns an error (Rangeindex because of empty arrivals)

## Future Sprints

#### D3 Charts
1. route page
    - route diagrams showing line, stops, current bus locations

2. stop page
    - dot column (like nobel prize chart) on arrival list showing frequency by hour
        - implement by concatenating the 3 nobel scripts into one external javascript and calling from route-base.html, passing the same {{arrivals_list_final_df|tojson}} to it
    - bar column for service frequency

#### import archival data
- in 'buses_summer2018' database
- in 'buses_fall018' database

#### Reliability Grade
1. ask Eric what the correct metric is (# of standard deviations for total start to end trip time?) e.g. how often does it get worse than the average 
2. compute on each page view, write to db?, write to route_config.py?
3. add to page
    - as letter grade and description, or
    - as literal: e.g. 'TODAY IS TYPICAL. TODAY IS WORSE THAN USUAL.'
    - dtop level metrics: - stop.html: THIS STATION USUALLY HAS DECENT SERVICE or THIS STATION HAS GOOD SERVICE TODAY or something like that.

#### Q.C. -- missed arrivals, duplicate arrivals

- **missing arrivals** - probably happening when approaching bus comes up as '2 min' and then disappears, never being observed as 'APPROACHING'
        - debugging: Missing buses that never were ‘APPROACHING’ the stop = do a query in jupyter of those that were 2 mins and then dissappeared
- **duplicate arrivals**--esp at early stops on the 87, e.g. http://0.0.0.0:5000/nj/87/stop/20931/history (see sept 20)



#### Draw Routes Along Street Network
1. Use Mapbox directions API?

#### Live-Update of Bus Positions 
1. update map positions every 3-5 sec and animate progress
    [https://medium.com/@Scarysize/the-moving-city-visualizing-public-transport-877f581ca96e](link)    

#### new data structure
- class Trip
    - mainly holds key:value pairs for {stop_id: call_time} and some metadata about the vehicle and operator
    - write a new 'buswatcher' that keeps an eye on all buses active on the route via NJT 'busesforroute' API call, isolates them (or drops them) to a stop through a proximity-based algorithm
    - proximity-based algorithm: uses shapely for the spatial processing (rather than postgres)
        - find nearest stop to a bus breadcrumb (and then log a stop when it gets under a threshold and starts to go up again)
        - filter these approaches for point of closest approach (by distance) + log that
        - possible technique: Nearest Neighbour Analysis — Geo-Python - AutoGIS documentation [link](https://automating-gis-processes.github.io/2017/lessons/L3/nearest-neighbour.html)     
    - compute travel times from stop to stop and log, allowing us to go back and compute travel time for any A to B along route


#### "playback" a trip
1. generate a list of runs, linked to 'playback' pages
2. API call that spits out geojson for all points in routelog for a single run, on a specific date
3. display on a page using mapbox live update [tutorial](https://www.mapbox.com/mapbox-gl-js/example/live-update-feature/)

#### setup slave to backup db    
- [howto](https://www.digitalocean.com/community/tutorials/how-to-move-a-mysql-data-directory-to-a-new-location-on-ubuntu-16-04)
   
#### new services data structure
1. class Service (based on GTFS)
2. class Service (built up from API)
    - Create a class for services, with tables in db
    - These get populated as the lines are loaded
    - Grabbers and webpages are smart and don't die if they try to grab a service that's not active
    - Hardcode the headsigns if they are ambigious 
    
#### schedule adherence / GTFS integration
- Can you show the delta between planned arrival time and actual arrival? I understand the bunching concern, but it seems like the avg rider would also be concerned about late arrivals. For instance, when I see a bus that usually has headways of 12-25 minutes, but has one instance of a 35 min headway, that seems like it should be called out similarly to how the bunching incidents are called out 
- http://simplistic.me/playing-with-gtfs.html
- module to create lookup table GTFS:Clever_Devices - timestamp_hr_min+run_id --> gtfs: trip_id+start_time so we can match routelog.run to gtfs.trip_id
- GTFS integration:  write a routine to match gtfs trip_id, start_time :: timestamp,run for first observation of a v in routelog series (e.g. map run to trip_id) -- either a machine learning model or something simpler 
   



