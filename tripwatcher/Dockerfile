# base python supervisor image
FROM praekeltfoundation/supervisor

# copy the supervisor conf file
ADD ./tripwatcher/tripwatcher.conf /etc/supervisor/conf.d/

# copy rest of code
COPY . .
