FROM python:3.6-alpine as base
FROM base as builder

RUN apk add --update supervisor && rm  -rf /tmp/* /var/cache/apk/*
ADD ./reportcard/supervisord/supervisord.conf  /etc/
ADD ./tripwatcher/tripwatcher.conf /etc/supervisor/conf.d/

RUN mkdir /install
WORKDIR /install
COPY ./tripwatcher/requirements.txt /requirements.txt
RUN pip install --install-option="--prefix=/install" -r /requirements.txt
FROM base
COPY --from=builder /install /usr/local
COPY . .
WORKDIR /

CMD ["supervisord", "-n"]
