FROM python:3.6

LABEL maintainer="Tim Akinbo <takinbo@timbaobjects.com>"

ADD . /app/
RUN pip install --no-cache-dir -r /app/requirements/prod.txt
RUN cd /app/ \
    && make babel-compile
WORKDIR /app/
CMD ["gunicorn","-c","gunicorn.conf","--bind=[::]:5000","apollo.wsgi:application"]
EXPOSE 5000
