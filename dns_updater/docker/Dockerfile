FROM python:3.6-alpine as base
FROM base as builder

ADD supervisord.conf  /etc/
ADD dns_updater.conf /etc/supervisor/conf.d/

RUN mkdir /install
WORKDIR /install
RUN pip install --install-option="--prefix=/install" requests
FROM base
COPY --from=builder /install /usr/local
WORKDIR /
COPY . .

CMD ["python", "/buswatcher/dns_updater/gandi-live-dns.py"]