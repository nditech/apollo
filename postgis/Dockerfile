FROM postgres:12
MAINTAINER Tim Akinbo <takinbo@timbaobjects.com>

RUN apt update && apt install -y postgis

COPY ./initdb-postgis.sh /docker-entrypoint-initdb.d/postgis.sh
