FROM dockerfile/ubuntu:precise

RUN apt-get update
RUN apt-get install -y python-dev build-essential python-setuptools
RUN easy_install pip virtualenv
