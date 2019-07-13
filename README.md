# NJ BusWatcher
**2019 july 12**


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

Docker deployment abandoned for now. Its easier and simpler for us to spend the 15 minutes deploying manually.

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
   
9. install conda
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
    git checkout development_branch
    ```
10. create a conda environment with the needed packages

    ```bash
    conda update -n base conda
    cd buswatcher/docker
    conda env create -f environment.yml
    conda activate buswatcher
    ```

    n.b. bug for some reason, in this process pandas doesn't get installed on OSX and needs to be installed manually after the build

#### frontend


11. get the linux software

    ```bash
    sudo apt-get install supervisor nginx 
    ```

12. install the front end config files

    ```bash 
    ./install_front_end.sh
    ```    
    (for full manual install, see instructions at end of this file )

13. install netdata (optional)
    use the DigitalOcean [tutorial](https://www.digitalocean.com/community/tutorials/how-to-set-up-real-time-performance-monitoring-with-netdata-on-ubuntu-16-04)

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

    So now, whenever you need to update the repo in the future simply 
    ```
    cd ~
    ./update.sh
    ```
    
    Try it now.
    
#### manual front end install


this follows the instructions [here](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xvii-deployment-on-linux) 


12. configure supervisor to run the www.py flask app

    ```bash
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
    ```
    
13. and the tripwatcher.py app

    ```bash
    sudo nano /etc/supervisor/conf.d/tripwatcher.conf
    ```
    contents

    ```bash
    [program:tripwatcher]
    command=/home/ubuntu/anaconda3/envs/buswatcher/bin/python tripwatcher.py
    directory=/home/ubuntu/buswatcher/buswatcher
    user=ubuntu
    autostart=true
    autorestart=true
    stopasgroup=true
    killasgroup=true
    ```

13. and the generator.py app

    ```bash
    sudo nano /etc/supervisor/conf.d/generator.conf
    ```
    contents

    ```bash
    [program:generator]
    command=/home/ubuntu/anaconda3/envs/buswatcher/bin/python generator.py --production
    directory=/home/ubuntu/buswatcher/buswatcher
    user=ubuntu
    autostart=true
    autorestart=true
    stopasgroup=true
    killasgroup=true
    ```

15. reload supervisor
    `sudo supervisorctl reload`

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
    Don't forget to reload nginx...
    
    ```sudo systemctl reload nginx``` 
    
    ...and open the firewall.
    
    ```sudo ufw allow 'Nginx HTTP'```

