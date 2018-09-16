### todo DEPLOY+TESTING 
[/]:# (todo DEPLOY+TESTING)
- deploy [latest master branch -- with caching](https://github.com/code4jc/buswatcher/tree/065fe941fe1a8742376e1d7c4782316f0a3e7169) -- maybe after next cleanup + commit -- and test on server. switch back to deployed_beta brannch

### todo BUGS
[/]:# (todo BUGS)
- #### setup way to override localhost as db_server
    - environment variables? 2 different pycharm runtime configurations?
    ```python
      import os
      os.environ['REPORTCARD_DEVELOPMENT'] = 'TRUE'
    
      then in the code (wherever db_setup is)
    
      if os.environ['REPORTCARD_DEVELOPMENT'] = 'TRUE':
          db_server = '192.168.1.181'
      else:
          db_server = 'localhost'
 
    ```
    if that doesnt work
    - using ? config.py
    - using a switch/argparse?
    - just hardcode it on a branch?
    
- arrivals board: often tables are incomplete -- buses are missing, or deltas seems ot be computed off of missing rows (Arrivals we know occured but are missing). is the error happening in sql, python, or jinja? -- when i see one debug and inspect back up the stack
- arrivals board: 3 min interval as bunching but not a 0 minute one as bunching… seems counter intuitive?

### todo DATA_MODEL
[/]:# (todo DATA_MODEL)
- services / responses to getRoutePoints depends on time of date, only returns routes that are currently in service. how to handle this?
- the route.path data structure still seems unwieldy. ask alex about it, and/or look at 87 xml response getrotepoints to fix parser - and flatten it?

### todo CONTENT+UX
[/]:# (todo CONTENT+UX)
- home page hero: 1 graf up front: Tell people why it’s currently hard to evaluate bus service, what you did to make it easy, and why it matters.
- tone: more pointed than “opportunities and challenges” language. "We made this site so you can tell how well the busses actually work. Knowing the status quo is critical to having a constructive discussion about how to improve service for all JC residents.”
- Clicking “check out the report cards” does nothing.
- Nine bus routes on bottom of page are ambiguous - are they buttons or not? Consider adding text above to the effect of “Click your route to see our analysis”
- put grade or grade color code on home page too

### todo ROUTE_REPORTs
[/]:# (todo ROUTE_REPORTs)
- Route page: Can you compare today to historical trends? TODAY IS TYPICAL. TODAY IS WORSE THAN USUAL.
- bunching board: "What are the trouble spots slowing service on the 119?" language is distracting.
- The route grades will help a lot. I think you want the grade to be the most obvious thing on the page so it’s clear WTF you’re looking at. The description of the route is nice but less important, especially since I think you already know about the route if you care enough to use the site.
- reliability rating / grade - % on time (based on how long average it is taking buses to run the whole route end to end -- looking at routereport?)
- I like the Bottlenecks list. Put the focus on the stops that need the most help. This should take precedence over “Choose Direction…” which I might consider replacing with a list of all of the stops do you don’t have to go through two drop downs to get to a stop page. Alternatively, replace the whole thing with a map interface that has RED icons for the bottleneck stops and GREEN ones for the good service stops, or some variation thereof.

### todo STOP_REPORTs
[/]:# (todo STOP_REPORTs)
- frequency of service: what was the average time between buses for each hour of the day during thie period?
- reliability: what was the average travel time from here to the end of the line during thie period?
- Stop page: add an overall assessment at the top. THIS STATION USUALLY HAS DECENT SERVICE or THIS STATION HAS GOOD SERVICE TODAY or something like that.
- Arriving Soon and Arrival History columns Not sure how to read them together. Presumably since this is a report card I don’t really care about the arriving soon times… I just care whether the service is good or not. If that’s the case, I would ditch arriving soon altogether, or perhaps put all arrivals (past and future) in one single list that’s organized ascending (past first).
- schedule adherence: Can you show the delta between planned arrival time and actual arrival? I understand the bunching concern, but it seems like the avg rider would also be concerned about late arrivals. For instance, when I see a bus that usually has headways of 12-25 minutes, but has one instance of a 35 min headway, that seems like it should be called out similarly to how the bunching incidents are called out.

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
