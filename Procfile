web: gunicorn -c gunicorn.conf --bind=[::]:$PORT apollo.wsgi:application
worker: celery -A apollo.tasks worker --loglevel=INFO --concurrency=2 --without-gossip
