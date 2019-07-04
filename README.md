# NJ BusWatcher
**26 june 2019**


### Overview

Buswatcher is a Python web app to collect bus position and stop arrival prediction data from several API endpoints maintained by NJTransit (via vendor Clever Devices), synthesize and summarize this information, and present to riders in a number of useful ways via a simple, interactive web application. Its implemented in Python using flask, pandas, and geopandas.


### Components

- **tripwatcher.py**. Fetches bus current locations for a route from the NJT API, creates a `Trip` instance for each, and populates it with `ScheduledStop` instances for each stop on the service its running, and a `BusPosition` instance for each observed position.
- **generator.py**. A cron-type daemon that does a bunch of batch jobs around the clock to manage the database load.
- **buswatcher.py** The flask app for routing incoming requests.
- **/lib** Core classes.
    - **DataBases.py**
        - *`Trip` Class*. The basis for all route performance metrics are Trips, represented in buswatcher by the `Trip` class. `Trip` instances are created by `tripwatcher.py` as needed to hold `BusPosition` instances (`BusPosition` is an inner class of `Trip`. `TripDB` instances handle writing to the database.
  

### Deployment

It's all dockerized now. Use `docker-compose` and build from the project root.

1. Deploy docker (see debugging crashing docker containers below)
2. Run generator --testmode --tasks minutely quarter_hourly hourly daily
Seed the reports folder. Otherwise things will probably break for up to 24 hours.
3. Setup DNS forwarding (Gandi control panel)
4. Setup a backup scheme for the database.

#### Debugging Crashing Docker Containers

Shell on running container

```
docker exec -it <container_id> /bin/bash
```
"Can’t start your container at all? If you’ve got a initial command or entrypoint that immediately crashes, Docker will immediately shut it back down for you. This can make your container unstartable, so you can’t shell in any more, which really gets in the way.

Fortunately, there’s a workaround: save the current state of the shut-down container as a new image, and start that with a different command to avoid your existing failures.

```
docker commit <container_id> my-broken-container &&
docker run -it my-broken-container /bin/bash
```
Have a failing entrypoint instead? There’s an entrypoint override command-line flag too." ([source](https://medium.com/@pimterry/5-ways-to-debug-an-exploding-docker-container-4f729e2c0aa8))



#### Manual MySQL Database Creation

(for testing)

```
sudo mysql -u root -p

mysql> CREATE database buses;
Query OK, 1 row affected (0.00 sec)

mysql> CREATE USER 'buswatcher'@'localhost' IDENTIFIED BY 'njtransit';
Query OK, 0 rows affected (0.00 sec)

mysql> GRANT ALL PRIVILEGES ON buses . * TO 'buswatcher'@'localhost';
Query OK, 0 rows affected (0.00 sec)

mysql> ALTER USER 'buswatcher'@'localhost' IDENTIFIED WITH mysql_native_password BY 'njtransit';
Query OK, 0 rows affected (0.00 sec)

mysql> flush privileges;
Query OK, 0 rows affected (0.00 sec)
```


### Version 2

Improvements over v1
- rewritten in Python 3
- new localization and stop assignment algorithm is based on geographicposition and stop proximity not API arrival predictions
- full SQLalchemy database implementation for easier mix and match backend
