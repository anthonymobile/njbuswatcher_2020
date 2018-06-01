# bus_report_card and busdumper

Two frameworks for interacting with, logging, and presenting raw data and summaries of bus location and arrival prediciton data from the NJ transit MyBusNow service -- but should work with any transit agency using the CleverDevices API.



## Bus Report Card
Web app that displays real-time and aggregated performance data for NJTransit bus routes.

### Usage

Specify a data source and a route number. Cron it persistently to build up a log of past observations of arrivals along the route, once per minute is usually best. 
```
python reportcard.py -s nj -r 119
```


### UX Concept

This is a sketch of what we hope to build out. (The OmniGraffle drawing is in the /ux folder of the repo.)

![the thing](doc/reportcard_ux/wireframe.png)



### Data and Metrics
The data collection is all being handled by the buswatcher project, and will pull from the API being developed there.

There are 3 separate sets of metrics that riders care about we need to calculate.

1. Frequency of service. How often does a bus stop at my corner? This is simply calculated by looking at how often any in-service bus passes a given stop on a particular route.
2. Travel time. How long is it taking buses to get from one stop to the next. What segments are contributing the most to delays along the line at any given instant, and over time?
3. Schedule adherence. Is the bus actually hitting its scheduled stops? This is more of an issue on less frequent routes, and its becoming less important as more people use apps to meet the bus. At rush time its often not at all important. But its pretty easy to do, comparing against GTFS timetables, so lets do it.


### Approach

- Adapted the code used in Buses.py and BusDB.py to talk to getStopPrediction in the CleverDevices API
- for a selected number of stops on a bus route, fetch current arrival predictions and log to a sqlite database
- perform analysis of three metrics above and present to user
    - key method is comparing instances of 'APPROACHING' predictions that indicate a bus arriving at the stop. intervals between these events indicate frequency of service at stops. progress of individual vehicles along route can be similar tracking by detecting these events at subsequent stops.
- as historical data set scales, log historical results to avoid re-processing



## busdumper

This will grab an entire transit system's worth of bus current locations (in this case, the entire NJTransit statewide system). Not actively working on this.


### Usage
It's worth checking to make sure your pipeline is working before trying to automate the data collection. Otherwise you are asking for a lot of nasty emails from your cron daemon.


```
python2 busdumper.py -s nj --save-raw buslocations.csv
```

####Logging to sqlite

This will simply start to append new observations to a file (absolute path e.g. ~/file) that will quickly become unmanageable. Not recommended for ongoing collection.
```
python busdumper.py -s nj sqlite --sqlite-file buslog.sqlite
```

#### Logging to MySQL

Recommended for ongoing data grabs and long-term storage with integrity (statewide grab is about TK GB/week as of 2018). Make sure you've created a user, and a database.

```
python2 busdumper.py -s nj --db-name {tk} --db-user {tk} --db-pw {not required} --db-host {default 127.0.0.1}
```


#### Logging to mongodb

Just starting to test if this is better for long-term storage of very large archives, but added support anyways. No support for remote or access-restricted databases yet, only local.

```
python2 busdumper.py -s nj mongo --mongo-name {tk}
```


### Ongoing Collection 

You want to cron it, any more than once a minute is probably overkill - though there are a couple of urban design use cases we've envisioned where finer-grained movements might be useful. Full paths always better in cron in my experience.

```bash
* * * * * /usr/bin/python /home/buswatcher/buswatcher.py -s nj mysql --db-name bus_position_log --db-user buswatcher --db-pw njtransit
```

For New Jersey, this will tuck in at around 100-150 GB a year in SQLite, snapping once a minute. YMMV with higher frequency or different databases. Currently, we have this setup on a Digital Ocean ubuntu 16 droplet, pushign the data to a MYsql database vault stored on Amazon S3 via a FUSE mount. Here are how-tos on [moving your database directory](https://www.digitalocean.com/community/tutorials/how-to-move-a-mysql-data-directory-to-a-new-location-on-ubuntu-16-04) and [connecting Ubuntu and S3](https://firefli.de/tutorials/s3fs-and-aws.html). 

### API
The API is intended as a scalable mechanism for exposing large repositories of position and prediction observations for analysis and queries.

####v1.0 (deprecated)
Implemented with flask and flask-mysql.

Available Routes:
http://buswatcher.code4jc.org/api-1.0
- /{n} - returns all the position reports for all vehicles for a given route over all time


####v1.1 (Under development)
Implemented with with flask-restful and sqlalchemy

Available Routes:
http://buswatcher.code4jc.org/api-1.1
- /route/{n} - all position reports, all vehicles, for route {n}, limit 50. This is jsut for inspection, testing services, etc.

Routes under development:

- /route/daily/{n} - all of the position reports since midnight local time for a given route.

- /bus/{n} - all the position reports for a specific  vehicle over all time. 
- /bus/daily/{n} 
- /bus/weekly/{n}


####v2.0 (TBD)
All of the above plus:
http://buswatcher.code4jc.org/api-2.0
- /route/monthly/{n}
- /route/yearly/{n}
- /route/history/{n}

- /bus/monthly/{n}
- /bus/yearly/{n}
- /bus/history/{n}

Implementation will be mostly batch processed by python scripts and served up as static files. Requests for anything older than the last week will be basically implemented with the same method as API v1.1 (Assuming that turns out faster)




