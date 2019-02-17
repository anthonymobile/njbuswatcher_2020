# from https://github.com/szelenka/shrink-linalg
FROM python:3.6-slim-jessie
MAINTAINER Scott Zelenka (szelenka)

COPY ./tripwatcher/library-dependencies.txt /tmp/library-dependencies.txt
COPY ./tripwatcher/requirements.txt /tmp/requirements.txt
RUN buildDeps='build-essential gcc gfortran python3-dev apt-utils' \
    && apt-get update \
    && apt-get install -y $buildDeps --no-install-recommends \
    && cat /tmp/library-dependencies.txt | egrep -v "^\s*(#|$)" | xargs apt-get install -y \
    && CFLAGS="-g0 -Wl,--strip-all -I/usr/include:/usr/local/include -L/usr/lib:/usr/local/lib" \
        /usr/local/bin/pip install \
        --no-cache-dir \
        --compile \
        --global-option=build_ext \
        --global-option="-j 4" \
        -r /tmp/requirements.txt \
    && apt-get purge -y --auto-remove $buildDeps \
    && rm -rf /var/lib/apt/lists/* \
    && rm -r \
        /tmp/requirements.txt \
        /tmp/library-dependencies.txt

# install requirements
WORKDIR /
COPY ./tripwatcher/requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

#### Install GEOS ####
# https://github.com/calendar42/docker-python-geos/blob/master/Dockerfile
ENV GEOS http://download.osgeo.org/geos/geos-3.6.2.tar.bz2
ENV PROCESSOR_COUNT 1
ADD $GEOS /install-postgis/
WORKDIR /install-postgis/geos-3.6.2/
RUN ./configure --enable-python && make -j $PROCESSOR_COUNT && make install
RUN ldconfig
RUN geos-config --cflags
RUN apt-get update && apt-get install -y binutils libproj-dev gdal-bin


# install shapely
COPY ./tripwatcher/requirements2.txt /requirements2.txt
RUN pip install -r /requirements2.txt

# copy project
COPY ./tripwatcher .

# add basic supervisor config
COPY ./tripwatcher/supervisord.conf /etc/supervisord.conf

# add tripwatcher supervisor profile
ADD ./tripwatcher/tripwatcher.conf /etc/supervisor/conf.d/


CMD ["supervisord", "-n"]