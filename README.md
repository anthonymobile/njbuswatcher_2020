# NJ BusWatcher
**2019 july 10**

# todos debugging

### docker-compose
- make sure we are using the same mysql version on both local (8) and docker-compose (?)
- export a new, clean enviroment.yml for /buswatcher/buswatcher/docker
```conda env export -n buswatcher > environment.yml```
- do we need to tell the db mysql container that we are using native password auth for `buswatcher` user on buses (see [this HOWTO](https://medium.com/@crmcmullen/how-to-run-mysql-8-0-with-native-password-authentication-502de5bac661) for mysql8/docker/native auth )

### debugging crashing docker containers

Shell on running container

```
docker exec -it <container_id> /bin/bash
```
"Can’t start your container at all? If you’ve got a initial command or entrypoint that immediately crashes, Docker will immediately shut it back down for you. This can make your container unstartable, so you can’t shell in any more, which really gets in the way.

Fortunately, there’s a workaround: save the current state of the shut-down container as a new image, and start that with a different command to avoid your existing failures.

```
docker commit <container_id> my-broken-container && docker run -it my-broken-container /bin/bash
```
Have a failing entrypoint instead? There’s an entrypoint override command-line flag too." ([source](https://medium.com/@pimterry/5-ways-to-debug-an-exploding-docker-container-4f729e2c0aa8))


-----

## Overview

Buswatcher is a Python web app to collect bus position and stop arrival prediction data from several API endpoints maintained by NJTransit (via vendor Clever Devices), synthesize and summarize this information, and present to riders in a number of useful ways via a simple, interactive web application. Its implemented in Python using flask, pandas, and geopandas.


### Version 2 Improvements
- rewritten in Python 3
- new localization and stop assignment algorithm is based on geographic position and stop proximity not API arrival predictions
- full SQLalchemy database implementation for easier mix and match backend


## Components
- **tripwatcher.py**. Fetches bus current locations for a route from the NJT API, creates a `Trip` instance for each, and populates it with `ScheduledStop` instances for each stop on the service its running, and a `BusPosition` instance for each observed position.
- **generator.py**. A cron-type daemon that does a bunch of batch jobs around the clock to manage the database load.
- **www.py** The flask app for routing incoming requests.
- **/lib** Core classes.
    - **DataBases.py**
        - *`Trip` Class*. The basis for all route performance metrics are Trips, represented in buswatcher by the `Trip` class. `Trip` instances are created by `tripwatcher.py` as needed to hold `BusPosition` instances (`BusPosition` is an inner class of `Trip`. `TripDB` instances handle writing to the database.
  

-----

# Deployment

## Deploy with docker

1. Add the Gandi LiveDNS API key to buswatcher/dns_updater/config.py in the repo
1. Build from the docker-compose.yml in the project root. Voila! Container magic.
1. Give generator about 30 minutes to seed the reports. Grades should show as pending in the interim, but some of the reports may have bugs (during alpha, we will fix)
1. Two volumes are important -- db_volume for the database and buswatcher_config will hold the nightly/hourly reports.

## Deploy manually

### backend

1. Assumes using EC2 Ubuntu instance. Set one up.
 
2. set the instance timezone
    ```bash
    sudo dpkg-reconfigure tzdata```
    
3. make sure you're up to date
    ```bash
    sudo apt-get update
    sudo apt-get upgrade
    ```
    likely only be a few updates.
4. configure ufw
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
    basically you want to answer yes to all the questions. pick the level of password annoyance you want to deal with. you'll have to hard code the buswatcher database password later so its up to you.

8. create the database user, with native_password auth otherwise python problems
    ```bash
    sudo mysql -u root -p
    mysql> CREATE USER 'buswatcher'@'localhost' IDENTIFIED BY 'njtransit';
    Query OK, 0 rows affected (0.00 sec)
    
    mysql> GRANT ALL PRIVILEGES ON buses . * TO 'buswatcher'@'localhost';
    Query OK, 0 rows affected (0.00 sec)
    
    mysql> ALTER USER 'buswatcher'@'localhost' IDENTIFIED WITH mysql_native_password BY 'njtransit';
    Query OK, 0 rows affected (0.00 sec)
    
    mysql> flush privileges;
    Query OK, 0 rows affected (0.00 sec)
    
    mysql> exit
    ```
    while the `buses` database doesn't exist yet, this will set things up so there's no problems when the buswatcher scripts do instantiate it later.
    
9. install conda
    ```bash
    cd ~
    mkdir tmp; cd tmp
    wget https://repo.anaconda.com/~~~~fill in yourself~~~~
    bash ./Anaconda3~~~~fill in yourself~~~~
    ```

10. clone the buswatcher repo
    ```bash
    cd ~
    git clone https://github.com/code4jc/buswatcher.git
    ```

11. if needed, checkout the proper branck
    ```bash
    cd buswatcher
    git checkout development_branch
    ```
10. create a conda environment with the needed packages

    ```bash
    conda update -n base conda
    cd buswatcher/docker
    conda create --name buswatcher -f environment.yml
    source activate buswatcher
    ```

    n.b. bug for some reason, in this process pandas doesn't get installed on OSX and needs to be isntalled manually after the build

#### frontend

this follows the instructions [here](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xvii-deployment-on-linux) 

11. get the linux software

    ```bash
    sudo apt-get install supervisor nginx 
    ```

12. configure supervisor to run the www.py flask app

    ```bash
    sudo nano /etc/supervisor/conf.d/www.conf
    ```

    and paste the following text in
    ```bash
    [program:reportcard]
    command=/home/ubuntu/anaconda3/envs/buswatcher/bin/gunicorn -b localhost:8000 -w 4 www:app
    directory=/home/ubuntu/buswatcher/buswatcher
    user=ubuntu
    autostart=true
    autorestart=true
    stopasgroup=true
    killasgroup=true
    ```
    then `sudo supervisorctl reload`
    

13. TK configure supervisor to run the tripwatcher.py app

14. TK configure supervisor to run the buswatcher.py app

    
15. config nginx as proxy server. you gotta keep the Russians away from gunicorn. unicorns are pretty.

    remove the default config
    ```bash
    sudo rm /etc/nginx/sites-enabled/default
    ```
    
    install a new one
    ```bash
    sudo nano /etc/nginx/sites-enabled/www
    ```
    with the following
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
    ```

    then `sudo service nginx reload` and open the firewall `sudo ufw allow 'Nginx HTTP'` and you should be good to go. 



16. updating your app is as easy as 1-2-3...4

```bash
cd ~/buswatcher
git pull
sudo supervisorctl stop www
sudo supervisorctl stop tripwatcher
sudo supervisorctl stop generator
sudo supervisorctl start www
sudo supervisorctl start tripwatcher
sudo supervisorctl start generator
```





### manual mysql db setup (w/o docker)

(for local testing)

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
