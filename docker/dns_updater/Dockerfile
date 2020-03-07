FROM python:3.6-alpine as base
FROM base as builder

RUN mkdir /install
WORKDIR /install
RUN pip install --install-option="--prefix=/install" requests
FROM base
COPY --from=builder /install /usr/local
WORKDIR /
COPY . .

RUN apk add --no-cache bash

# todo how to safely copy the API key to ./buswatcher/dns_updater/config.py
# maybe cat it to the file?
# echo "api_secret = '---my_secret_API_KEY----'" > ./buswatcher/dns_updater/config.py


CMD ["python", "/dns_updater/gandi-live-dns.py"]