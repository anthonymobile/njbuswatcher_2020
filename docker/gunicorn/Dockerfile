# docker run -it --entrypoint /bin/bash $IMAGE_NAME -s
#
# buswatcher (gunicorn,flask)
#
# https://medium.com/@chadlagore/conda-environments-with-docker-82cdc9d25754
FROM continuumio/miniconda3

ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt update
RUN apt install -y build-essential

RUN conda config --set channel_priority flexible
RUN conda update -n base -c defaults conda

ADD ./docker/environment.yml /tmp/environment.yml
RUN conda env create -f /tmp/environment.yml

# Pull the environment name out of the environment.yml
RUN echo "source activate $(head -1 /tmp/environment.yml | cut -d' ' -f2)" > ~/.bashrc
ENV PATH /opt/conda/envs/$(head -1 /tmp/environment.yml | cut -d' ' -f2)/bin:$PATH
ENV PYTHONPATH /buswatcher:PYTHONPATH

# copy project
WORKDIR /
RUN mkdir buswatcher
COPY . ./buswatcher

# copy the proper database config over for docker deployment (replaces the development version)
COPY ./docker/DBconfig.py ./buswatcher/buswatcher/lib/DBconfig.py

WORKDIR /buswatcher/buswatcher
