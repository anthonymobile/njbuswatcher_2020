# pull new code and restart services

cd ~/buswatcher
git pull
sudo supervisorctl stop www tripwatcher generator
sudo supervisorctl start www tripwatcher generator