# https://medium.com/@chadlagore/conda-environments-with-docker-82cdc9d25754
FROM continuumio/miniconda3
ADD environment.yml /tmp/environment.yml
RUN conda env create -f /tmp/environment.yml
# Pull the environment name out of the environment.yml
RUN echo "source activate $(head -1 /tmp/environment.yml | cut -d' ' -f2)" > ~/.bashrc
ENV PATH /opt/conda/envs/$(head -1 /tmp/environment.yml | cut -d' ' -f2)/bin:$PATH


# set work directory
WORKDIR /

# copy entrypoint.sh
COPY ./reportcard/entrypoint.sh /usr/src/reportcard/entrypoint.sh

# copy project
COPY . /usr/src/reportcard/

# run entrypoint.sh
ENTRYPOINT ["/usr/src/reportcard/entrypoint.sh"]
