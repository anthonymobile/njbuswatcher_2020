# generator
# https://medium.com/@chadlagore/conda-environments-with-docker-82cdc9d25754

FROM continuumio/miniconda3

ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt update
RUN apt install -y build-essential

RUN conda config --set channel_priority flexible
RUN conda update -n base -c defaults conda

# get environment from app folder
ADD ./docker/gunicorn/environment.yml /tmp/environment.yml
# create env and cleanup
# https://jcristharif.com/conda-docker-tips.html
RUN conda env create -f /tmp/environment.yml \
    && conda clean -afy \
    && find /opt/conda/ -follow -type f -name '*.a' -delete \
    && find /opt/conda/ -follow -type f -name '*.pyc' -delete \
    && find /opt/conda/ -follow -type f -name '*.js.map' -delete 


# Pull the environment name out of the environment.yml
RUN echo "source activate $(head -1 /tmp/environment.yml | cut -d' ' -f2)" > ~/.bashrc
ENV PATH /opt/conda/envs/$(head -1 /tmp/environment.yml | cut -d' ' -f2)/bin:$PATH

# copy project
WORKDIR /
RUN mkdir buswatcher
COPY . ./buswatcher

# copy the proper database config over for docker deployment (uses the docker server url 'db')
COPY ./docker/DBconfig.py ./buswatcher/buswatcher/lib/DBconfig.py

