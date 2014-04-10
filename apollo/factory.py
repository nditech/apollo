from celery import Celery
from flask import Flask, request

from .core import babel, db, mail
from .helpers import register_blueprints


def create_app(package_name, package_path, settings_override=None):
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

    babel.init_app(app)
    db.init_app(app)
    mail.init_app(app)

    @babel.localeselector
    def get_locale():
        return request.accept_languages \
            .best_match(app.config.get('LANGUAGES', {}).keys())

    register_blueprints(app, package_name, package_path)

    return app


def create_celery_app(app=None):
    app = app or create_app('apollo', '')
    celery = Celery(__name__, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery
