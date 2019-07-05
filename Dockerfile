FROM python:3.6-alpine

LABEL maintainer="Tim Akinbo <takinbo@timbaobjects.com>"

ADD requirements/prod.txt /app/requirements.txt
RUN set -ex \
        && apk add --no-cache --virtual .build-deps \
            build-base \
        && apk add --no-cache openblas-dev \
            libffi-dev \
            libxml2-dev \
            libxslt-dev \
            postgresql-dev \
            libmagic \
        && apk add --no-cache --repository http://dl-cdn.alpinelinux.org/alpine/edge/testing/ geos-dev \
        && pip install -r /app/requirements.txt \
        && cd /app/ \
        && find /usr -depth \
            \( -type f -a -name '*.pyc' -o -name '*.pyo' \) \
            -exec rm -rf '{}' + \
        && runDeps="$(scanelf --needed --nobanner --recursive /usr \
            | awk '{ gsub(/,/, "\nso:", $2); print "so:" $2 }' \
            | sort -u \
            | xargs -r apk info --installed \
            | sort -u)" \
        && apk add --virtual .python-rundeps $runDeps \
        && apk del --purge .build-deps \
        && rm -rf /root/.cache
ADD . /app/
RUN cd /app/ \
    && pybabel compile -d /app/apollo/translations/
WORKDIR /app/
CMD ["gunicorn","-c","gunicorn.conf","--bind=[::]:5000","apollo.wsgi:application"]
EXPOSE 5000
