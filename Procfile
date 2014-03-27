web: uwsgi --http-socket :$PORT --cpu-affinity 1 --master --gevent 2000 --listen 1000 --disable-logging --processes 2 --virtualenv . --module apollo.wsgi:application
