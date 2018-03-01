# -*- coding: utf-8 -*-
from celery import current_app
from celery.bin import worker
from flask_script import Command


class CeleryWorker(Command):

    """Run the celery worker"""

    def __call__(self, app=None, *args, **kwargs):
        a = current_app._get_current_object()
        w = worker.worker(app=a)

        options = {
            'loglevel': 'INFO',
            'concurrency': 2,
            'without-gossip': True
        }
        options.update(kwargs)

        w.run(*args, **options)
