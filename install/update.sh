# todo 1 script to
cd ~/buswatcher
git pull
sudo supervisorctl stop www tripwatcher generator
sudo supervisorctl start www tripwatcher generator