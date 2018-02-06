#web: uwsgi --http-socket [::]:$PORT --cpu-affinity 1 --master --listen 1000 --disable-logging --processes 2 --max-requests 100 --module apollo.wsgi:application
web: gunicorn --workers=2 apollo.wsgi:application
worker: celery -A apollo.tasks worker --loglevel=INFO --concurrency=2 --without-gossip
