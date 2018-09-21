### todo ASAP 
[/]:# (todo ASAP)
- stops: hourly frequency figure out how to get the data out for display in jinja
- make bus boxes at bottoms linked buttons (not jsut the #s)
- colorize the grades based on actual grade (see code in route_servicepicker)
- fix BUG on yesterday query (from old commit? or just google againg)


### todo NEXT 
[/]:# (todo DEPLOY+TESTING)
-stops: put all arrivals (past and future) in one single list that’s organized descending (predictions first).
-stops: 3 min interval as bunching but not a 0 minute one as bunching… seems counter intuitive?.
-route:reliability(grade, really) average travel time from here to the end of the line during the period (think through efficient algorithm for finding + calculating when bus x arrives at stop y down the line on same run -- cross reference it in the two stopreports and routewatch with run id)

### todo CONTENT+UX
[/]:# (todo CONTENT+UX)

### todo ROUTE_REPORTs
[/]:# (todo ROUTE_REPORTs)
- Route page: Can you compare today to historical trends? TODAY IS TYPICAL. TODAY IS WORSE THAN USUAL.
- The route grades will help a lot. I think you want the grade to be the most obvious thing on the page so it’s clear WTF you’re looking at. The description of the route is nice but less important, especially since I think you already know about the route if you care enough to use the site.
- reliability rating / grade - % on time (based on how long average it is taking buses to run the whole route end to end -- looking at routereport?)
- I like the Bottlenecks list. Put the focus on the stops that need the most help. This should take precedence over “Choose Direction…” which I might consider replacing with a list of all of the stops do you don’t have to go through two drop downs to get to a stop page. Alternatively, replace the whole thing with a map interface that has RED icons for the bottleneck stops and GREEN ones for the good service stops, or some variation thereof.

### todo STOP_REPORTs
[/]:# (todo STOP_REPORTs)
- Stop page: add an overall assessment at the top. THIS STATION USUALLY HAS DECENT SERVICE or THIS STATION HAS GOOD SERVICE TODAY or something like that.
- schedule adherence: Can you show the delta between planned arrival time and actual arrival? I understand the bunching concern, but it seems like the avg rider would also be concerned about late arrivals. For instance, when I see a bus that usually has headways of 12-25 minutes, but has one instance of a 35 min headway, that seems like it should be called out similarly to how the bunching incidents are called out

### todo DATA_MODEL
[/]:# (todo DATA_MODEL)
- add indices to all the tables?
- services / responses to getRoutePoints depends on time of date, only returns routes that are currently in service. how to handle this?
- the route.path data structure still seems unwieldy. ask alex about it, and/or look at 87 xml response getrotepoints to fix parser - and flatten it?

### todo MAPS
[/]:# (todo MAPS)
- Convert BusWatcher to flask-bootstrap (fit index into a common header/footer)
- outline leaflet-based map architecture:
    - [flask leaflet demo github](adwhit/flask-leaflet-demo)
    - [How can I pass data from Flask to JavaScript in a template? - Stack Overflow](https://stackoverflow.com/questions/11178426/how-can-i-pass-data-from-flask-to-javascript-in-a-template)

### todo API
[/]:# (todo API)
- build the API for arrivals [tutorial](https://programminghistorian.org/en/lessons/creating-apis-with-python-and-flask)
- build the API for bus locations
- create data sources on Stae to ingest and archive both


### todo MISC
[/]:# (todo FUTURE)
- convert to python 3
- import dump.gz --> process 2prune_ tables by keeping only records with pt='APPROACHING' and migrate to current tables
- setup daily mysql db backup or slave mirror on little Lenovo
