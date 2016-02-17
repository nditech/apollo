from cachetools import cached
from celery import Celery
from flask import Flask, request
from flask.ext.sslify import SSLify
from raven import Client
from raven.contrib.celery import register_signal, register_logger_signal

from apollo.core import babel, cache, db, mail, sentry
from apollo.helpers import register_blueprints
from importlib import import_module


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
    mail.init_app(app)

    if app.config.get('SSL_REQUIRED'):
        SSLify(app)

    @babel.localeselector
    def get_locale():
        return request.accept_languages \
            .best_match(app.config.get('LANGUAGES', {}).keys())

    register_blueprints(app, package_name, package_path)

    if register_all_blueprints:
        for configured_app in app.config.get('APPLICATIONS'):
            register_blueprints(
                app, configured_app, import_module(configured_app).__path__)

    return app


@cached(cache={})
def create_celery_app(app=None):
    app = app or create_app('apollo', '', register_all_blueprints=False)
    celery = Celery(__name__, broker=app.config['CELERY_BROKER_URL'])

    # configure exception logging
    client = Client(app.config.get('SENTRY_DSN', ''))
    register_logger_signal(client)
    register_signal(client)

    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery
