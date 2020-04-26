FROM tiangolo/meinheld-gunicorn-flask:python3.7

ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone


# HOW TO CREATE THE ENVIRONMENT INSIDE THE CONTAINER?
## https://medium.com/@chadlagore/conda-environments-with-docker-82cdc9d25754
#FROM continuumio/miniconda3
RUN apt update
RUN apt install -y build-essential
RUN conda config --set channel_priority flexible
RUN conda update -n base -c defaults conda
ADD ./docker/environment.yml /tmp/environment.yml
RUN conda env create -f /tmp/environment.yml
# Pull the environment name out of the environment.yml
RUN echo "source activate $(head -1 /tmp/environment.yml | cut -d' ' -f2)" > ~/.bashrc
ENV PATH /opt/conda/envs/$(head -1 /tmp/environment.yml | cut -d' ' -f2)/bin:$PATH
ENV PYTHONPATH /app:PYTHONPATH


## copy project
WORKDIR /
COPY ./app /app

# copy the proper database config over for docker deployment (replaces the development version)
COPY ./docker/DBconfig.py ./app/app/lib/DBconfig.py
#
#WORKDIR /app/app
