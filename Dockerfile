FROM python:3.6-alpine

LABEL maintainer="Tim Akinbo <takinbo@timbaobjects.com>"

ADD Pipfile* /app/
RUN set -ex \
        && apk add --no-cache --virtual .build-deps \
            build-base \
        && apk add --no-cache openblas-dev \
            libffi-dev \
            libxml2-dev \
            libxslt-dev \
            postgresql-dev \
            libmagic \
        && pip install pipenv \
        && cd /app/ \
        && PIP_NO_BUILD_ISOLATION=false pipenv sync --sequential \
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
    && pipenv run pybabel compile -d /app/apollo/translations/
WORKDIR /app/
CMD ["pipenv","run","gunicorn","-c","gunicorn.conf","--bind=[::]:5000","apollo.wsgi:application"]
EXPOSE 5000
