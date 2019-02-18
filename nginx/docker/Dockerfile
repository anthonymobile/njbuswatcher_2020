FROM nginx:1.15.0-alpine

RUN rm /etc/nginx/conf.d/default.conf
COPY ./nginx/docker/nginx.conf /etc/nginx/conf.d

# copy project
WORKDIR /
RUN mkdir buswatcher
COPY . ./buswatcher