# copy to home folder of instance

# cp /buswatcher/install/update.sh ~/
# chmod 755 update.sh
# ./update.sh

cd ~/buswatcher
git pull
sudo supervisorctl stop www tripwatcher generator
sudo supervisorctl start www tripwatcher generator