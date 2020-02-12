# NJ BusWatcher
**updated 2020 feb 12**


## Overview

Buswatcher is a Python web app to collect bus position and stop arrival prediction data from several API endpoints maintained by NJTransit (via vendor Clever Devices), synthesize and summarize this information, and present to riders in a number of useful ways via a simple, interactive web application. Its implemented in Python using flask, pandas, and geopandas.

#### Version 2 Improvements
- rewritten in Python 3
- new localization and stop assignment algorithm is based on geographic position and stop proximity not API arrival predictions
- full SQLalchemy database implementation for easier mix and match backend


## Known Issues and TODOs

- various `#todo` items are tagged in the source comments. these need to be extracted, cataloged, prioritized
- There are a number of issues with how we are modeling some of the route geometry and schedule anomalies, that are documented [here](https://github.com/code4jc/buswatcher/issues/19), [here](https://github.com/code4jc/buswatcher/issues/18), and [here](https://github.com/code4jc/buswatcher/issues/17).
- some optimization opportunities and database tuning would help, although the system scales statewide fairly well on a modest EC2 instance.
- archiving of grades and reports is needed
- graphs would probably be more informative and less processor-heavy than aggreagate stats/summaries for most views
- dockerize deployment (there is a dead version in earlier commits that never fully worked)
- the API could use some sort of securing/key/token
- the API should expose more useful stuff, including archival data, reports, etc.
- the reporting systems is really burdensome and could use a rethink
- need to add certbot/ssl setup to Getting Started (its jut a few steps. (install certbot + use a different config file for nginx, can copy from current live instance)
- securing netdata is not described here, and it isnt straightforward. we can probably drop it altogether once development winds down and EC2 isntance sizing is more or less finalized.
  
## Getting Started

Docker deployment abandoned for now. Its easier and simpler for us to spend the 15 minutes deploying manually.

#### backend stuff

1. Assumes using EC2 Ubuntu instance. Set one up. Dont forget to assign a security group that lets ssh, http, https, and 19999 (netdata if you want it) through.
 
2. set the instance timezone
    ```bash
    sudo dpkg-reconfigure tzdata```
    
3. make sure you're up to date
    ```bash
    sudo apt-get update
    sudo apt-get upgrade
    ```

4. install and configure ufw
    ```bash
    sudo ufw allow ssh
    sudo ufw enable
    ```
    ignore the 'disrupt connection' warning 
    ```
    sudo ufw status
    ```
    you should see something like this
    ```
    Status: active
    To                         Action      From
    --                         ------      ----
    22                         ALLOW       Anywhere
    22 (v6)                    ALLOW       Anywhere (v6)
    ```
5. change ssh port (optional). its often a good idea to move your ssh server over to a non-standard port. i usually pick a ZIP code i know and use the last 4 digits. i'll leave this one to you. just for godssake - dont forget to open the new port in the firewall with ufw before you restart the ssh server or you've bricked your new server. 

6. change the hostname (also optional). i like to, jsut because i hate anonymous AWS hostnames
    ```bash
    sudo nano /etc/hostname
    ```
    you'll need to reboot the instance and log back in
    ```bash 
    sudo shutdown -r now
    ```

7. install and configure mysql (make sure its 5.7)
    ```bash
    sudo apt-get install mysql-server 
    ```
    pick a password for your mysql root user and dont forget it!
    ```bash
    sudo mysql_secure_installation
    ```
    basically you want to answer no to the first (validate password plugin), and yes to the rest of the questions. pick the level of password annoyance you want to deal with. you'll have to hard code the buswatcher database password later so its up to you.

8. create the database user, with native_password auth otherwise python problems
    ```bash
    sudo mysql -u root -p
    mysql> CREATE USER 'buswatcher'@'localhost' IDENTIFIED BY 'njtransit';
    
    mysql> GRANT ALL PRIVILEGES ON buses . * TO 'buswatcher'@'localhost';
    
    mysql> ALTER USER 'buswatcher'@'localhost' IDENTIFIED WITH mysql_native_password BY 'njtransit';
    
    mysql> CREATE DATABASE buses;
    
    mysql> flush privileges;
    
    mysql> exit
    ```
   
9. install conda (n.b. version numbers change)
    ```bash
    cd ~
    mkdir tmp; cd tmp
    wget https://repo.anaconda.com/archive/Anaconda3-2019.03-Linux-x86_64.sh
    bash ./Anaconda3-2019.03-Linux-x86_64.sh
    ```

10. clone the buswatcher repo
    ```bash
    cd ~
    git clone https://github.com/code4jc/buswatcher.git
    ```

11. if needed, checkout the proper branck
    ```bash
    cd buswatcher
    git checkout development
    ```
10. create a conda environment with the needed packages

    ```bash
    conda update -n base conda
    cd buswatcher/install
    conda env create -f environment.yml
    conda activate buswatcher
    ```

    n.b. on OSX development environments, pandas doesn't get installed here and needs to be installed manually after the build

#### frontend

11. get the linux software

    ```bash
    sudo apt-get install supervisor nginx 
    ```

12. install the front end config files

    ```bash 
    ./install_front_end.sh
    ```
    
    - what this script does (if you need to do it manually)
        - configures supervisor to run the www.py flask app
            - ```bash
                sudo nano /etc/supervisor/conf.d/www.conf
                ```
    
                and paste the following text in
                ```bash
                [program:www]
                command=/home/ubuntu/anaconda3/envs/buswatcher/bin/gunicorn -b localhost:8000 -w 4 www:app
                directory=/home/ubuntu/buswatcher/buswatcher
                user=ubuntu
                autostart=true
                autorestart=true
                stopasgroup=true
                killasgroup=true              
                
                
        - configures supervisor to run tripwatcher.py app

            - ```bash
                sudo nano /etc/supervisor/conf.d/tripwatcher.conf
                ```
                and paste the following text in
            
                ```bash
                [program:tripwatcher]
                command=/home/ubuntu/anaconda3/envs/buswatcher/bin/python tripwatcher.py
                directory=/home/ubuntu/buswatcher/buswatcher
                user=ubuntu
                autostart=true
                autorestart=true
                stopasgroup=true
                killasgroup=true
                
                
        - configures supervisor to run generator.py app

            - ```bash
                sudo nano /etc/supervisor/conf.d/generator.conf
                ```
                and paste the following text in
            
                ```bash
                [program:generator]
                command=/home/ubuntu/anaconda3/envs/buswatcher/bin/python generator.py --production
                directory=/home/ubuntu/buswatcher/buswatcher
                user=ubuntu
                autostart=true
                autorestart=true
                stopasgroup=true
                killasgroup=true
                
                
                

    
        - configures nginx as proxy server. you gotta keep the Russians away from gunicorn. unicorns are pretty.
            - remove the default config
            `sudo rm /etc/nginx/sites-enabled/default`  
            - install a new one
            `sudo nano /etc/nginx/sites-enabled/www`
            with the following contents
            ```bash
            server {
            # listen on port 80 (http)
            listen 80;
            server_name www;
        
            location / {
                # forward application requests to the gunicorn server
                proxy_pass http://localhost:8000;
                proxy_redirect off;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            }
        
            location /static {
                # handle static files directly, without forwarding to the application
                alias /home/ubuntu/buswatcher/buswatcher/static;
                expires 30d;
            }
            }   
   
       - reloads supervisor
        `sudo supervisorctl reload`
       - restarts nginx
       `sudo systemctl reload nginx`
       - opens firewall
       `sudo ufw allow 'Nginx HTTP'`
            
13. install netdata (optional) according to the DigitalOcean [tutorial](https://www.digitalocean.com/community/tutorials/how-to-set-up-real-time-performance-monitoring-with-netdata-on-ubuntu-16-04)

16. dns_updater -- copy your API key to config.py and setup a cron job

    ```bash
    */5 * * * * /home/ubuntu/buswatcher/dns_updater/gandi-live-dns.py >/dev/null 2>&1
    
    ```

16. Install the update script

    ```bash
    cp /buswatcher/install/update.sh ~/
    chmod 755 update.sh
    ./update.sh
    ```

    So now, whenever you need to update the repo and restart all the services in the future simply 
    ```
    cd ~
    ./update.sh
    ```
    
    Try it now.
    




## Architecture


### Route Geometry Model

Core classes (see DBconfig.py for formal definitions)
 - A `Trip` represents everything we know about a particular bus making a journey, and is uniquely identified by a string concatenated from the vehicle id, the run number, and the current date. (e.g. `5463_323_20200202`). `Trip` has a one-to-many parent relationship with both `ScheduledStop` and `BusPosition`.
 - A `ScheduledStop` represents a stop along a route, for a particular vehicle, on a particular run. `ScheduledStop` has a many-to-one child relationship with `Trip`. These are created when a `Trip` is created (by `Trip.__init` if I recall).
- A `BusPosition` represents an observation of a bus at a particular point in time.
 `BusPosition` has a many-to-one child relationship with `Trip`.  `BusPosition` has a one-to-one child relationship with `ScheduledStop` (TKverify this).

   

### Components


Everything in `/buswatcher`

These three programs are run by supervisor more or less persistently.

- **www.py** The flask app for routing incoming requests.
- **generator.py**. Batch processor daemon. Has ability to run minutely, hourly, daily tasks. For instance, once a day downloads and pickles route geometry and builds route reports overnight when bus tracking is mostly idle.
- **tripwatcher.py**. Fetches bus current locations for a route from the NJT API, creates a `Trip` instance for each, and populates it with `ScheduledStop` instances for each stop on the service its running, and a `BusPosition` instance for each observed position.

Libraries and config files.

- **/alembic** Database migration files.
- **/config** Top level is user-defined settings. Nothing should break if you change these, but will rebuild.
    -   collection_descriptions.json—define the cities and routes to be tracked by this instance. Ok to change while running.
    -   route_descriptions.json—master definition of routes. bad things happen if you try to track a route not listed here.
    -   period_descriptions.json—labels for the various periods.
    -   grade_descriptions.json—bins and labels for the letter grades.
    - **/reports**—system-generated route reports. dont touch. 
    - **/route_geometry**—system-generated route geometry pickle files. dont touch. 
- **/lib** Core classes.
    - **API.py**—implements the external web API   
    - **DataBases.py**—the ORM models.
    - **DBconfig.py**—user-defined database URL
    - **Generators.py**—classes to create and dump all the various reports for routes/stops/metrics
    - **NJTransitAPI.py**—main fetch and parse from the NJTransit Clever Devices API
    - **RouteScan.py**—main processor for incoming bus positions after pre-processing by NJTransitAPI. Mostly focused on localizing a `BusPosition` instance to the nearest `ScheduledStop`
- **/locust** Load testing stuff.
- **/static** Static stuff served by nginx
    - **/gen**
    - **/images**
    - **/maps** Javascript to render client-size maps
    - **/mdb** CSS stuff
- **/templates** jinja page templates
     
     
### Other stuff

**/dns_updater** Updates domain IP at Gandi.net to host current
**/install** Setup helpers, env config, etc.

   

## API

The JS maps all use the external API. It is available for general use also. Stem for all is `https://www.njbuswatcher.com/api/v1/maps/{endpoint}?rt={route}`

#### /vehicles
`rt=` Positions of buses currently on the route.

#### waypoints
`/api/v1/maps/waypoints` Route geometry as a series of points.

#### stops
`/api/v1/maps/waypoints` Stop locations.


## Maintenance
 
Occasionally you may want / need to manually refresh the route reports. 
there will be a need to run the ```generator.py``` daily or hourly batch jobs manually. (For instance after adjusting the grade criteria.) The ```--test``` switch supports this and requires a list of ```--tasks``` as well. e.g. The following commands let you start the job, disown it, send it to the background, and then logout while it continues and finishes on its own.
```bash
$ python generator.py --test --tasks daily hourly
$ disown -h %1
$ bg 1
$ logout
```
Note that the tasks will be run in the order you list them. It's generally recommended to run the longest interval tasks (e.g. daily) first.

