FROM continuumio/miniconda3

# copy conda environment
ADD ./tripwatcher/environment.yml /tmp/environment.yml

RUN conda env create -f /tmp/environment.yml
# Pull the environment name out of the environment.yml
RUN echo "source activate $(head -1 /tmp/environment.yml | cut -d' ' -f2)" > ~/.bashrc
ENV PATH /opt/conda/envs/$(head -1 /tmp/environment.yml | cut -d' ' -f2)/bin:$PATH

# install supervisor
RUN apt-get update --fix-missing && \
    apt-get install -y supervisor

# add basic supervisor config
COPY ./reportcard/supervisord/supervisord.conf /etc/supervisord.conf

# copy the app supervisor conf file
COPY ./tripwatcher/tripwatcher.conf /etc/supervisor/conf.d/

# copy rest of code
COPY . .

CMD ["supervisord", "-n"]
