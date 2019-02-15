FROM ubuntu:latest

MAINTANER Your Name "youremail@domain.tld"

RUN apt-get update -y && \
    apt-get install -y python-pip python-dev supervisor nginx

# Add sudo
RUN apt-get -y install sudo

# Add user ubuntu with no password, add to sudo group
RUN adduser --disabled-password --gecos '' ubuntu
RUN adduser ubuntu sudo
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers
USER ubuntu
WORKDIR /home/ubuntu/
RUN chmod a+rwx /home/ubuntu/
#RUN echo `pwd`

# configure ufw (we like be safe from Ruskies)
RUN sudo ufw allow ssh
RUN sudo ufw enable

# change the hostname--because i hate anonymous AWS hostnames
COPY dockerconfig/hostname /etc/

#todo install and configure mysql (SEPARATELY)
# docker run --name mysql -d -e MYSQL_RANDOM_ROOT_PASSWORD=yes \
  #    -e MYSQL_DATABASE=buses -e MYSQL_USER=buswatcher \
  #    -e MYSQL_PASSWORD=njtransit \
  #    mysql/mysql-server:5.7




# install conda
RUN wget https://repo.continuum.io/archive/Anaconda3-5.0.1-Linux-x86_64.sh
RUN bash Anaconda3-5.0.1-Linux-x86_64.sh -b
RUN rm Anaconda3-5.0.1-Linux-x86_64.sh
# Set path to conda
#ENV PATH /root/anaconda3/bin:$PATH
ENV PATH /home/ubuntu/anaconda3/bin:$PATH
# Update Anaconda packages
RUN conda update conda
RUN conda update anaconda
RUN conda update --all

# create a conda environment with the needed packages
RUN create --name buswatcher python=3 mysql-connector-python pandas flask flask_cors django git
RUN source activate buswatcher
RUN conda install -c conda-forge flask-assets gunicorn

#install a couple loose ends (todo are they in conda-forge?)
RUN pip install geojson Flask-Bootstrap4

# clone the buswatcher repo
WORKDIR /home/ubuntu
RUN git clone https://github.com/code4jc/buswatcher.git

# configure supervisor to run the tripwatcher.py scraper
COPY dockerconfig/tripwatcher.conf /etc/supervisor/conf.d/
RUN sudo supervisorctl reload

# configure supervisor to run the reportcard.py flask app
COPY dockerconfig/reportcard.conf /etc/supervisor/conf.d/
RUN sudo supervisorctl reload

# config nginx as proxy server. you gotta keep the Russians away from gunicorn. unicorns are pretty.
COPY dockerconfig/reportcard /etc/nginx/sites-enabled/
RUN sudo service nginx reload
RUN sudo ufw allow 'Nginx HTTP'

# open the ports
EXPOSE 80
EXPOSE 443


# run command w/ sample env variables to pass and port mappings
#docker run --name buswatcher -d -p 8000:5000 --rm -e SECRET_KEY=my-secret-key \
#    -e MAIL_SERVER=smtp.googlemail.com -e MAIL_PORT=587 -e MAIL_USE_TLS=true \
#    -e MAIL_USERNAME=<your-gmail-username> -e MAIL_PASSWORD=<your-gmail-password> \
#    --link mysql:dbserver \
#    -e DATABASE_URL=mysql+pymysql://microblog:<database-password>@dbserver/microblog \
#    microblog:latest
