#### backend stuff

1. Assumes using EC2 Ubuntu instance. Set one up. Dont forget to assign a security group that lets ssh, http, https, and 19999 (netdata if you want it) through.
2. set the instance timezone 
    ```bash
    sudo dpkg-reconfigure tzdata
    ```
    
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

6. change the hostname (also optional). i like to, if only because i hate anonymous AWS hostnames
    ```bash
    sudo nano /etc/hostname
    ```
    you'll need to reboot the instance
    ```bash 
    sudo shutdown -r now
    ```
    
    And log back in.

7. install and configure mysql (make sure its 5.7)
    ```bash
    sudo apt-get install mysql-server 
    ```
    pick a password for your mysql root user and dont forget it!
    ```bash
    sudo mysql_secure_installation
    ```
    basically you want to answer no to the first (validate password plugin), and yes to the rest of the questions. pick the level of password annoyance you want to deal with. this is only for root access, you'll create a used for the buswatcher separately in the next step.

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
   
9. install the latest version of Anaconda (n.b. version numbers change)
    ```bash
    cd ~
    mkdir tmp; cd tmp
    wget https://repo.anaconda.com/archive/Anaconda3-2019.03-Linux-x86_64.sh
    bash ./Anaconda3-2019.03-Linux-x86_64.sh
    ```
    Make sure to use the default installation path `/home/ubuntu/anaconda3`

10. clone the buswatcher repo
    ```bash
    cd ~
    git clone https://github.com/code4jc/buswatcher.git
    ```

11. if testing instance, checkout the `development` branch
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

    - n.b. on OSX development environments, pandas doesn't get installed here and needs to be installed manually after the build
    - n.b. may have to install gcc first `sudo apt-get install gcc`

#### frontend

11. get the linux software

    ```bash
    sudo apt-get install supervisor nginx 
    ```

12. install the front end config files

    ```bash 
    cd /home/ubuntu/buswatcher
    install/install_front_end.sh
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

16. dns_updater -- copy your API key to `dns_updater/config.py` and setup a cron job with `crontab -e` and paste the following into it.

    ```bash
    */5 * * * * /usr/bin/python3 /home/ubuntu/buswatcher/dns_updater/gandi-live-dns.py >/dev/null 2>&1
    ```

16. Install the update script

    ```bash
    cp ~/buswatcher/install/update.sh ~/
    cd ~
    chmod 755 update.sh
    ./update.sh
    ```

    So now, whenever you need to update the repo and restart all the services in the future simply 
    ```
    cd ~
    ./update.sh
    ```
    
    Try it now.