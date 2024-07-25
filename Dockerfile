FROM python:3.11.9
ARG ENV

LABEL maintainer="Tim Akinbo <takinbo@timbaobjects.com>"

ADD requirements/ /app/requirements/
ADD build.sh /app/
RUN /app/build.sh
ADD . /app/
RUN cd /app/ \
    && make babel-compile
WORKDIR /app/
CMD ["gunicorn","-c","gunicorn.conf","--bind=[::]:5000","apollo.wsgi:application"]
EXPOSE 5000
