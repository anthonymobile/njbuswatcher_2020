FROM python:3.6-alpine as base
FROM base as builder

RUN mkdir /install
WORKDIR /install
RUN pip install --install-option="--prefix=/install" requests
FROM base
COPY --from=builder /install /usr/local
WORKDIR /
COPY . .


CMD ["python", "/buswatcher/buswatcher/dns_updater/gandi-live-dns.py"]