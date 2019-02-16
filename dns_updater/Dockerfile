FROM python:3.6-alpine as base
FROM base as builder

RUN apk add --update supervisor && rm  -rf /tmp/* /var/cache/apk/*
ADD ./reportcard/supervisord/supervisord.conf  /etc/
ADD ./dns_updater/dns_updater.conf /etc/supervisor/conf.d/

RUN mkdir /install
WORKDIR /install
COPY ./dns_updater/requirements.txt /requirements.txt
RUN pip install --install-option="--prefix=/install" -r /requirements.txt
FROM base
COPY --from=builder /install /usr/local
COPY . .
WORKDIR /

CMD ["supervisord", "-n"]
