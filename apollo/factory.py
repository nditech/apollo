# -*- coding: utf-8 -*-
from cachetools import cached
from importlib import import_module

from celery import Celery
from flask import Flask, current_app, g, json, request
from flask_babelex import gettext as _
from flask_security import current_user
from flask_sslify import SSLify
from flask_uploads import configure_uploads
from raven.base import Client
from raven.contrib.celery import register_signal, register_logger_signal
from redis import ConnectionPool, Redis

from apollo.core import (
    babel, cache, db, fdt_available, debug_toolbar, mail, migrate, sentry,
    uploads)
from apollo.helpers import register_blueprints


TASK_DESCRIPTIONS = {
    'apollo.locations.tasks.import_locations': _('Import Locations'),
    'apollo.participants.tasks.import_participants': _('Import Participants'),
    'apollo.submissions.tasks.init_submissions': _('Create Checklists')
}


def get_redis_pool():
    if 'redis_pool' not in g:
        if 'REDIS_URL' not in current_app.config:
            raise KeyError(
                'Improperly configured: REDIS_URL missing from config')
        g.redis_pool = ConnectionPool.from_url(
            current_app.config.get('REDIS_URL')
        )

    return g.redis_pool


def create_app(
    package_name, package_path, settings_override=None,
    register_all_blueprints=True
):
    """Returns a :class:`Flask` application instance configured with common
    functionality for the Overholt platform.

    :param package_name: application package name
    :param package_path: application package path
    :param settings_override: a dictionary of settings to override
    :param register_security_blueprint: flag to specify if the Flask-Security
                                        Blueprint should be registered.
                                        Defaults to `True`.
    """
    app = Flask(package_name, instance_relative_config=True)
    app.config.from_object('apollo.settings')
    app.config.from_object(settings_override)

    sentry.init_app(app)
    babel.init_app(app)
    cache.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    configure_uploads(app, uploads)

    if app.config.get('SSL_REQUIRED'):
        SSLify(app)

    if app.config.get('DEBUG') and fdt_available:
        debug_toolbar.init_app(app)

    # don't reregister the locale selector
    # if we already have one
    if babel.locale_selector_func is None:
        @babel.localeselector
        def get_locale():
            # get a list of available language codes,
            # starting from the current user's selected
            # language
            language_codes = set()
            if not current_user.is_anonymous:
                if current_user.locale:
                    return current_user.locale

            language_codes.update(app.config.get('LANGUAGES', {}).keys())

            return request.accept_languages \
                .best_match(language_codes)

    register_blueprints(app, package_name, package_path)

    if register_all_blueprints:
        for configured_app in app.config.get('APPLICATIONS'):
            register_blueprints(
                app, configured_app, import_module(configured_app).__path__)

    from .sse import sse
    app.register_blueprint(sse, url_prefix='/stream')

    # clean up the Redis pool
    @app.teardown_appcontext
    def cleanup_redis(*args, **kwargs):
        redis_pool = g.pop('redis_pool', None)
        if redis_pool is not None:
            redis_pool.disconnect()

    return app


@cached(cache={})
def create_celery_app(app=None):
    app = app or create_app('apollo', None, register_all_blueprints=False)
    celery = Celery(__name__, broker=app.config['CELERY_BROKER_URL'])

    # configure exception logging
    client = Client(app.config.get('SENTRY_DSN', ''))
    register_logger_signal(client)
    register_signal(client)

    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True
        task_info = {}
        track_started = True
        redis_instance = None

        def __call__(self, *args, **kwargs):
            with app.app_context():
                self.redis_instance = Redis(connection_pool=get_redis_pool())
                return TaskBase.__call__(self, *args, **kwargs)

        def on_failure(self, exc, task_id, args, kwargs, einfo):
            with app.app_context():
                channel = kwargs.get('channel')
                payload = {
                    'id': task_id,
                    'status': _('FAILED'),
                    'progress': self.task_info,
                    'description': TASK_DESCRIPTIONS.get(self.request.task),
                    'quit': True,
                }
                if channel is not None:
                    self.redis_instance.publish(channel, json.dumps(payload))
                    self.redis_instance = None

        def on_success(self, retval, task_id, args, kwargs):
            with app.app_context():
                channel = kwargs.get('channel')
                payload = {
                    'id': task_id,
                    'status': _('COMPLETED'),
                    'progress': self.task_info,
                    'description': TASK_DESCRIPTIONS.get(self.request.task),
                    'quit': True,
                }
                if channel is not None:
                    self.redis_instance.publish(channel, json.dumps(payload))
                    self.redis_instance = None

        def update_task_info(self, **kwargs):
            request = self.request
            channel = request.kwargs.get('channel')
            self.task_info.update(**kwargs)
            self.update_state(meta=self.task_info)

            task_metadata = self.backend.get_task_meta(request.id)
            payload = {
                'id': request.id,
                'status': _('RUNNING'),
                'progress': task_metadata.get('result'),
                'description': TASK_DESCRIPTIONS.get(self.request.task)
            }
            if channel is not None:
                self.redis_instance.publish(channel, json.dumps(payload))

    celery.Task = ContextTask
    return celery
