FROM nginx:latest

RUN rm /etc/nginx/nginx.conf
COPY nginx.conf /etc/nginx/

RUN rm /etc/nginx/conf.d/default.conf
COPY reportcard.conf /etc/nginx/conf.d/

COPY ./static ./static


# Nginx will listen on this port
EXPOSE 443