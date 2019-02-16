# base python supervisor image
FROM praekeltfoundation/supervisor

# install the requirements

# copy the supervisor conf file
ADD ./tripwatcher/tripwatcher.conf /etc/supervisor/conf.d/

# copy rest of code
COPY . .




# base python supervisor image
FROM praekeltfoundation/supervisor

WORKDIR /home
COPY ./tripwatcher/requirements.txt /home
RUN pip install --no-cache-dir -r requirements.txt

# copy the supervisor conf file
ADD ./tripwatcher/supervisord/tripwatcher.conf /etc/supervisor/conf.d/

# copy rest of code
COPY . .
