web: uwsgi --http-socket [::]:$PORT --cpu-affinity 1 --master --gevent 2000 --listen 1000 --disable-logging --processes 2 --max-requests 100 --virtualenv . --module apollo.wsgi:application
worker: celery -A apollo.tasks worker --loglevel=INFO --concurrency=2 --without-gossip
