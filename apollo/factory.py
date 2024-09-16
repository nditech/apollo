# -*- coding: utf-8 -*-
import json
import typing
from importlib import import_module

import sentry_sdk
from cachetools import cached
from celery import Celery, signals
from depot.manager import DepotManager
from flask import Flask, request
from flask_babel import gettext as _
from flask_login import current_user
from flask_security import SQLAlchemyUserDatastore, MailUtil
from flask_sslify import SSLify
from flask_uploads import configure_uploads
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

from apollo import models, settings
from apollo.api import hooks as jwt_hooks
from apollo.core import (
    babel,
    cors,
    db,
    debug_toolbar,
    fdt_available,
    jwt_manager,
    mail,
    migrate,
    red,
    security,
    uploads,
)
from apollo.helpers import register_blueprints
from apollo.security_ext_forms import DeploymentLoginForm

TASK_DESCRIPTIONS = {
    'apollo.locations.tasks.import_locations': _('Import Locations'),
    'apollo.participants.tasks.import_participants': _('Import Participants'),
    'apollo.submissions.tasks.init_submissions': _('Generate Checklists'),
    'apollo.users.tasks.import_users': _('Import Users'),
    'apollo.submissions.tasks.init_survey_submissions': _('Generate Surveys'),
}


def configure_image_storage(base_config: typing.Dict) -> None:
    # depots should only be configured once
    if not DepotManager.get('images'):
        configuration = base_config.copy()
        if settings.ATTACHMENTS_USE_S3:
            configuration.update({
                'depot.region_name': settings.AWS_IMAGES_REGION,
                'depot.bucket': settings.AWS_IMAGES_BUCKET,
            })
        else:
            configuration.update({
                'depot.storage_path': str(settings.image_upload_path)
            })

        DepotManager.configure('images', configuration)


def setup_attachment_storages() -> None:
    if DepotManager.get() is None:
        base_config = {}
        if settings.ATTACHMENTS_USE_S3:
            base_config.update({
                'depot.backend': 'depot.io.boto3.S3Storage',
                'depot.access_key_id': settings.AWS_ACCESS_KEY_ID,
                'depot.secret_access_key': settings.AWS_SECRET_ACCESS_KEY,
                'depot.region_name': settings.AWS_DEFAULT_REGION,
                'depot.endpoint_url': settings.AWS_ENDPOINT_URL,
                'depot.bucket': settings.AWS_DEFAULT_BUCKET,
            })
        else:
            base_config.update({
                'depot.backend': 'depot.io.local.LocalFileStorage',
                'depot.storage_path': str(settings.base_upload_path),
            })

        # TODO: configure default storage?
        configure_image_storage(base_config)


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

    class ApolloMailUtil(MailUtil):
        def send_mail(self, template, subject, recipient, sender, body, html, **kwargs):
            from apollo.tasks import send_email

            send_email.delay(
                subject=subject,
                sender=sender,
                recipients=[recipient],
                body=body
            )

    def _before_send(event, hint):
        with app.app_context():
            if current_user and not current_user.is_anonymous:
                deployment = current_user.deployment
                current_event = getattr(current_user, 'event', None)
            else:
                deployment = None
                current_event = None

            extra = event.setdefault("extra", {})
            extra.setdefault("deployment", getattr(deployment, "name", "N/A"))
            extra.setdefault("event", getattr(current_event, "name", "N/A"))

        return event

    cors.init_app(app)
    db.init_app(app)
    jwt_manager.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    red.init_app(app)
    sentry_sdk.init(
        dsn=app.config.get("SENTRY_DSN"),
        debug=app.config.get("DEBUG"),
        release=app.config.get("VERSION"),
        send_default_pii=True,
        integrations=[
            FlaskIntegration(transaction_style="url")
        ],
        before_send=_before_send
    )
    user_datastore = SQLAlchemyUserDatastore(db, models.User, models.Role)
    security.init_app(
        app, user_datastore, mail_util_cls=ApolloMailUtil, login_form=DeploymentLoginForm,
        register_blueprint=register_all_blueprints)
    configure_uploads(app, uploads)

    # set up JWT callbacks
    jwt_manager.expired_token_loader(jwt_hooks.process_expired_token)
    jwt_manager.invalid_token_loader(jwt_hooks.process_invalid_token)
    jwt_manager.revoked_token_loader(jwt_hooks.process_revoked_token)
    jwt_manager.token_in_blocklist_loader(
        jwt_hooks.check_if_token_is_blocklisted)

    if app.config.get('SSL_REQUIRED'):
        SSLify(app)

    if app.config.get('DEBUG') and fdt_available:
        debug_toolbar.init_app(app)

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

    babel.init_app(app, locale_selector=get_locale)
    register_blueprints(app, package_name, package_path)

    if register_all_blueprints:
        for configured_app in app.config.get('APPLICATIONS'):
            register_blueprints(
                app, configured_app, import_module(configured_app).__path__)

    # set up processing for attachments
    setup_attachment_storages()

    return app


@cached(cache={})
def create_celery_app(app=None):
    app = app or create_app('apollo', None, register_all_blueprints=False)
    celery = Celery(__name__, broker=app.config['CELERY_BROKER_URL'])

    # configure exception logging
    @signals.celeryd_init.connect
    def init_sentry(**_kwargs):
        sentry_sdk.init(
            dsn=app.config.get("SENTRY_DSN"),
            debug=app.config.get("DEBUG"),
            release=app.config.get("VERSION"),
            integrations=[
                CeleryIntegration(
                    propagate_traces=True
                )
            ]
        )

    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True
        task_info = {}
        track_started = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

        def on_failure(self, exc, task_id, args, kwargs, einfo):
            with app.app_context():
                channel = kwargs.get('channel')
                payload = {
                    'id': task_id,
                    'status': _('FAILED'),
                    'progress': self.task_info,
                    'description': TASK_DESCRIPTIONS.get(self.request.task, _('Task')),
                    'quit': True,
                }

                if channel is not None:
                    red.publish(channel, json.dumps(payload))

                    # leave result in Redis and set/renew the expiration
                    red.lpush(channel, json.dumps(payload))
                    red.expire(channel, app.config.get('TASK_STATUS_TTL'))

        def on_success(self, retval, task_id, args, kwargs):
            with app.app_context():
                channel = kwargs.get('channel')
                payload = {
                    'id': task_id,
                    'status': _('COMPLETED'),
                    'progress': self.task_info,
                    'description': TASK_DESCRIPTIONS.get(self.request.task, _('Task')),
                    'quit': True,
                }

                if channel is not None:
                    red.publish(channel, json.dumps(payload))

                    # leave result in Redis and set/renew the expiration
                    red.lpush(channel, json.dumps(payload))
                    red.expire(channel, app.config.get('TASK_STATUS_TTL'))

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
                'description': TASK_DESCRIPTIONS.get(self.request.task, _('Task'))
            }

            if channel is not None:
                red.publish(channel, json.dumps(payload))

    celery.Task = ContextTask
    return celery
