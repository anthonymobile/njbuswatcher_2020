# base python supervisor image
FROM praekeltfoundation/supervisor

# install the requirements
WORKDIR /home
COPY requirements.txt /home
RUN pip install --no-cache-dir -r requirements.txt

# copy the supervisor conf file
ADD ./dns_updater/tripwatcher.conf /etc/supervisor/conf.d/

# copy rest of code
COPY . .
