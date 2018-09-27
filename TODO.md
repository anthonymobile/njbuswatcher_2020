# Bugs, Ongoing Work, + Future Development

## Critical Bugs/Issues
- responsive: looks terrible on iOS
- ReportCard.Stop.get_hourly_frequency
    - replace 'nan' with 0 or 'n/a'  
- stop.html
    - trap [fatal errors like this](http://0.0.0.0:5000/nj/119/stop/31858/daily) -- is it just a 119 thing?
- create data sources on Stae to ingest and archive 87 and 119 positions
- Setup replication to slave for data backup

## Ongoing Work
1. API
    - build an API [tutorial](https://programminghistorian.org/en/lessons/creating-apis-with-python-and-flask) that dumps raw data needed to generate views in client javascript
        - arrivals by route / stop / period
1. Finalize current release
    - Finish refactor work to eliminate the stop picker, e.g. populate stop lists for all services at bottom of route page in columns
    - Develop simple route and stop grade calculator (e.g. add an overall assessment at the top.
        - route.html: TODAY IS TYPICAL. TODAY IS WORSE THAN USUAL. 
        - stop.html: THIS STATION USUALLY HAS DECENT SERVICE or THIS STATION HAS GOOD SERVICE TODAY or something like that.
        - grade based on average end-to-end travel time - e.g. how often does it get worse than the average (some statistical measure of on-time performance)
1. New services data structure
    - Because the API doesn't return services in service list that are not current in operation...
    - Create a class for services, with tables in db
    - These get populated as the lines are loaded
    - Grabbers and webpages are smart and don't die if they try to grab a service that's not active
    - Hardcode the headsigns if they are ambigious 
1. Live maps
    - mapbox GL javascript in route.html
        - one piece that loads a static geoJSON of just a single route extracted from the big [transitland geojson file](https://transit.land/feed-registry/operators/o-dr5-nj~transit)
        - another piece that fetches current vehicle positons from the Clever Devices getBusesForRoute api and parses the XML
1. New trip data structure
    - new class that represents a trip
    - built up from both routelog and arrival_log, or through API calls thorugh a new watcher
        - key fields include lat, lon, adjacent stops + distances, vehicle, run_id, ????
        - throw out or tag stop calls/arrivals
        - compute travel times from stop to stop and log, allowing us to go back and compute travel time for any A to B along route
    - new localization scheme
        - grab positions every 60 sec or more - routewatcher
        - filter by proximity to stops - log v, timestamp, stop, distance to stop
        - filter these approaches for point of closest approach (by distance) + log that
    
    
## Non-Critical Bugs/Issues

- BusAPI.Route
    - data structure seems unwieldy, look for opportunities to flatten if possible
- ReportCard.Stop.get_arrivals
    - **missing arrivals** - probably happening when approaching bus comes up as '2 min' and then disappears, never being observed as 'APPROACHING'
        - debugging: Missing buses that never were ‘APPROACHING’ the stop = do a query in jupyter of those that were 2 mins and then dissappeared
    - **duplicate arrivals**--esp at early stops on the 87, e.g. http://0.0.0.0:5000/nj/87/stop/20931/history (see sept 20)

## Long-term Work

1. Database optimization: add relevant indices to all tables, ensure that not keeping any useless observations (e.g. non-"APPROACHING" arrival predictions)
1. Migrate to Python 3
1. Migrate archived data (in 'buses_summer2018' database)
1. schedule adherence 
    - Can you show the delta between planned arrival time and actual arrival? I understand the bunching concern, but it seems like the avg rider would also be concerned about late arrivals. For instance, when I see a bus that usually has headways of 12-25 minutes, but has one instance of a 35 min headway, that seems like it should be called out similarly to how the bunching incidents are called out 
    - http://simplistic.me/playing-with-gtfs.html
    - module to create lookup table GTFS:Clever_Devices - timestamp_hr_min+run_id --> gtfs: trip_id+start_time so we can match routelog.run to gtfs.trip_id
1. GTFS integration 
    - write a routine to match gtfs trip_id, start_time :: timestamp,run for first observation of a v in routelog series (e.g. map run to trip_id) -- either a machine learning model or something simpler 


