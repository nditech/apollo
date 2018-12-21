FROM alpine:3.7

LABEL maintainer="Tim Akinbo <takinbo@timbaobjects.com>"

ADD Pipfile* /app/
RUN set -ex \
        && apk add --no-cache --virtual .build-deps \
            build-base \
            libxml2-dev \
            libxslt-dev \
            python3-dev \
            postgresql-dev \
            linux-headers \
        && apk add --no-cache --virtual .python-deps python3 libmagic \
        && python3 -m ensurepip \
        && rm -r /usr/lib/python*/ensurepip \
        && pip3 install --upgrade pip setuptools \
        && if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi \
        && if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi \
        && pip install pipenv \
        && cd /app/ \
        && PIP_NO_BUILD_ISOLATION=false pipenv install --sequential \
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
