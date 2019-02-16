FROM python:3

# install supervisor
RUN apt-get update --fix-missing && \
    apt-get install -y supervisor

# add basic supervisor config
COPY ./reportcard/supervisord/supervisord.conf /etc/supervisord.conf

# copy the app supervisor conf file
COPY ./dns_updater/dns_updater.conf /etc/supervisor/conf.d/

WORKDIR /usr/src/app

COPY ./dns_updater/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# run supervisor
CMD ["supervisord", "-n"]