# TODO

## Current (WEEK OF OCT 16)
1. nginx/gunicorn config: nginx "1270 no live upstreams while connecting to upstream" error --> https://stackoverflow.com/questions/49767001/how-to-solve-nginx-no-live-upstreams-while-connecting-to-upstream-client
1. ** bug: just after midnight: when there are no arrivals, stops page returns an error (Rangeindex because of empty arrivals)
2. test whether new indeing working - if so, backup old database and dump on buswatcher.code4jc.org


## Future Work (Weeklong Projects)
1.  Grades: Develop simple route and stop grade calculator (e.g. add an overall assessment at the top.
        - route.html: TODAY IS TYPICAL. TODAY IS WORSE THAN USUAL. 
        - stop.html: THIS STATION USUALLY HAS DECENT SERVICE or THIS STATION HAS GOOD SERVICE TODAY or something like that.
        - grade based on average end-to-end travel time - e.g. how often does it get worse than the average (some statistical measure of on-time performance)

1. postgres support
    - add/rewrite postgres support for all db classes (look back at early commits -- had it for BusAPI, fairly similar except minor create table changes), as it will add advanced geoprocessing capaiblities

1. Setup replication to slave for data backup
    - fix slave server: get back in as root and create mountpoint directory for /mnt/db
    - reinstall mysql-server `sudo apt-get install mysql-server`
    - move the mysql database to /mnt/db - [howto](https://www.digitalocean.com/community/tutorials/how-to-move-a-mysql-data-directory-to-a-new-location-on-ubuntu-16-04)
    - configure mysql slave [howto](https://www.digitalocean.com/community/tutorials/how-to-set-up-master-slave-replication-in-mysql)
    - stop mysql on slave [howto](https://www.electricmonk.nl/log/2016/11/06/very-fast-mysql-slave-setup-with-zero-downtime-using-rsync/) `sudo /etc/init.d/mysql stop`
    - login to master and rsync db binaries to slave, overwriting: `sudo rsync -Sa --progress --delete --exclude=mastername* --exclude=master.info --exclude=relay-log.info /mnt/db/mysql root@192.168.1.181:/var/lib`
    - ALT TO ABOVE: simply archive buses to dump or a new table and start a new one, then start the replication on the slave (only slave backup going forward)
    
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
        - filter by proximity to stops - log v, timestamp, stop, distance to stop - using MYSQL spatial [howto](https://www.percona.com/blog/2013/10/21/using-the-new-mysql-spatial-functions-5-6-for-geo-enabled-applications/)
        - filter these approaches for point of closest approach (by distance) + log that
    
    
## Non-Critical Bugs/Issues

- fix database tables: More efficient table structure for positions, routelog, arrivallog
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


