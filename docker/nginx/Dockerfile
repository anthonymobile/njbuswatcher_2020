# based on https://testdriven.io/blog/dockerizing-flask-with-postgres-gunicorn-and-nginx/

FROM nginx:alpine

RUN rm /etc/nginx/conf.d/default.conf
COPY ./docker/nginx/nginx.conf etc/nginx/conf.d

# timezone
RUN apk update
RUN apk upgrade
RUN apk add ca-certificates && update-ca-certificates
RUN apk add --update tzdata
ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN rm -rf /var/cache/apk/*

# copy project
WORKDIR /
RUN mkdir buswatcher
COPY . ./buswatcher