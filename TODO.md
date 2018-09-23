
### todo NEW ROUTE_SERVICESTOPLIST
[/]:# (todo ASAP)

- replace the dropdown w/ route dashboard 
    - pass a new object to render (or in routereport?
    - it shows all the stops plus current arrival predictions / bus locations?

### todo RELIABILITY GRADE 
[/]:# (todo RELIABILITY GRADE)
- travel time summary: for lower half of route_servicesstoplist.html
    1. select * from routelog_119 for entire_day sort by timestamp
    2. split by run (which will automaically split them by v too)
    3. simply subtract the first row timestamp from the last row
    4. could also arbitrarily ocmpute from a midpoint, or other ?
    5. resample -- average / mean for each hour (like in the stops hourly_frequency)
    
- reliability rating / grade - % on time
    - convert the travel time into a "is this run better or worse that average" rating - based that RUN's history? or that hours' history?

- activate the index page grades

### todo BUG CLEANUP + Q.C. 
[/]:# (todo BUG CLEANUP + Q.C.)

- hourly_frequency: replace 'nan' in jinja ('nan mins')
- trap fatal errors like this (http://0.0.0.0:5000/nj/119/stop/31858/daily) -- is it just a 119 thing?
- stops: 3 min interval as bunching but not a 0 minute one as bunching… seems counter intuitive?.
- bug: duplicate arrivals esp at early stops on the 87, e.g. http://0.0.0.0:5000/nj/87/stop/20931/history (see sept 20)
- make bus boxes at bottoms linked buttons (not jsut the #s) (PITA)
- stops: put all arrivals (past and future) in one single list that’s organized descending (predictions first).

### todo ROUTE_SERIVCEPICKER UX OVERHAUL
[/]:# (todo ROUTE_REPORTs)
- Route page: Can you compare today to historical trends? TODAY IS TYPICAL. TODAY IS WORSE THAN USUAL.
- make the grade to be the most obvious thing on the page so it’s clear WTF you’re looking at
- Alternatively, replace the whole thing with a map interface that has RED icons for the bottleneck stops and GREEN ones for the good service stops, or some variation thereof.

### todo BUILD API 
[/]:# (todo API)
- build an API that dumps raw data needed to generate views in client javascript
    - bus positions by route / period
    - arrivals by route / stop / period
    - [tutorial](https://programminghistorian.org/en/lessons/creating-apis-with-python-and-flask)
    - create data sources on Stae to ingest and archive both

### todo STOP UX OVERHAUL
[/]:# (todo STOP_REPORTs)
- Stop page: add an overall assessment at the top. THIS STATION USUALLY HAS DECENT SERVICE or THIS STATION HAS GOOD SERVICE TODAY or something like that.

### todo STOP SCHEDULE ADHERENCE
- schedule adherence: Can you show the delta between planned arrival time and actual arrival? I understand the bunching concern, but it seems like the avg rider would also be concerned about late arrivals. For instance, when I see a bus that usually has headways of 12-25 minutes, but has one instance of a 35 min headway, that seems like it should be called out similarly to how the bunching incidents are called out
- module to create lookup table GTFS:Clever_Devices - timestamp_hr_min+run_id --> gtfs: trip_id+start_time so we can match routelog.run to gtfs.trip_id

### todo MAPS
[/]:# (todo MAPS)
- us the TransitLand GeoJSON stuff as a starter kit: https://transit.land/feed-registry/operators/o-dr5-nj~transit
- Convert BusWatcher to flask-bootstrap (fit index into a common header/footer)
- outline leaflet-based map architecture:
    - [flask leaflet demo github](adwhit/flask-leaflet-demo)
    - [How can I pass data from Flask to JavaScript in a template? - Stack Overflow](https://stackoverflow.com/questions/11178426/how-can-i-pass-data-from-flask-to-javascript-in-a-template)

### todo OPTIMIZATION
[/]:# (todo OPTIMIZATION)
- add indices to all the tables in create_table
- services / responses to getRoutePoints depends on time of date, only returns routes that are currently in service. how to handle this?
- the route.path data structure still seems unwieldy. ask alex about it, and/or look at 87 xml response getrotepoints to fix parser - and flatten it?
- convert to python 3
- import dump.gz --> process 2prune_ tables by keeping only records with pt='APPROACHING' and migrate to current tables
- setup daily mysql db backup or slave mirror on little Lenovo
