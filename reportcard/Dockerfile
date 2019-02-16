FROM alpine:3.3
MAINTAINER Shawn McElroy <shawn@skift.io>

RUN apk add --no-cache supervisor

# install requirements
WORKDIR /home
RUN pip install --upgrade pip
COPY ./reportcard/requirements.txt /home
RUN pip install --no-cache-dir -r requirements.txt

# add basic supervisor config
COPY ./reportcard/supervisord/supervisord.conf /etc/supervisord.conf

# copy the app supervisor conf file
COPY ./reportcard/supervisord/reportcard.conf /etc/supervisor/conf.d/


CMD ["supervisord", "-n"]

