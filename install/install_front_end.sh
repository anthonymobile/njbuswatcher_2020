# this follows the instructions [here](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xvii-deployment-on-linux)

# 11. get the linux software
sudo apt-get install supervisor nginx

# 12. configure supervisor to run the www.py flask app
sudo cp install/www.conf /etc/supervisor/conf.d/www.conf

# 13. configure supervisor to run the tripwatcher.py
sudo cp install/tripwatcher.conf /etc/supervisor/conf.d/tripwatcher.conf

# 14. configure supervisor to run the generator.py
sudo cp install/generator.conf /etc/supervisor/conf.d/generator.conf

sudo supervisorctl reload

# 15. config nginx as proxy server. you gotta keep the Russians away from gunicorn. unicorns are pretty.
sudo rm /etc/nginx/sites-enabled/default
sudo cp install/www /etc/nginx/sites-enabled/www
sudo systemctl reload nginx
sudo ufw allow 'Nginx HTTP'
