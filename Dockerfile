FROM alpine:3.4

MAINTAINER Tim Akinbo <takinbo@timbaobjects.com>

ADD . /app/
RUN set -ex \
        && apk add --no-cache --virtual .build-deps \
            --repository http://dl-3.alpinelinux.org/alpine/edge/community/ \
            build-base \
            libxml2-dev \
            libxslt-dev \
            python-dev \
            openblas-dev \
            py-pip \
            linux-headers \
        && apk add --no-cache --virtual .python-deps \
            --repository http://dl-3.alpinelinux.org/alpine/edge/community/ \
            python \
            py-setuptools \
            libmagic \
        && cd /app/ \
        && rm Dockerfile* circle.yml fabfile.py \
        && mv Procfile.docker Procfile \
        && ln -s /usr/include/locale.h /usr/include/xlocale.h \
        && pip install numpy==1.11.1 uwsgi==2.0.13 \
        && pip install -r /app/requirements.txt \
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
        && rm -rf ~/.cache \
        && pybabel compile -d /app/apollo/translations/

WORKDIR /app/
CMD ["honcho","start"]
EXPOSE 5000
