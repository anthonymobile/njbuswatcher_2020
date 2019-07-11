# todo write this script




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

    then `sudo systemctl reload nginx` and open the firewall `sudo ufw allow 'Nginx HTTP'` and you should be good to go.
