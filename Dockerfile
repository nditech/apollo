FROM ubuntu:precise

MAINTAINER Tim Akinbo <takinbo@timbaobjects.com>

RUN apt-get update
RUN apt-get upgrade -y

RUN apt-get install -y python-dev build-essential python-setuptools
RUN easy_install pip virtualenv

ADD README /app/
ADD setup.py /app/
ADD requirements.txt /app/
ADD apollo/ /app/
ADD doc/ /app/
