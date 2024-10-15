# -*- coding: utf-8 -*-
import typing
from importlib import import_module

import sentry_sdk
from celery import Celery, Task
from depot.manager import DepotManager
from flask import Flask, has_request_context, request
from flask_babel import gettext as _
from flask_login import current_user
from flask_security import MailUtil, SQLAlchemyUserDatastore
from flask_sslify import SSLify
from flask_uploads import configure_uploads
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

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
    menu,
    metrics,
    migrate,
    red,
    security,
    uploads,
)
from apollo.helpers import register_blueprints
from apollo.security_ext_forms import DeploymentLoginForm

TASK_DESCRIPTIONS = {
    "apollo.locations.tasks.import_locations": _("Import Locations"),
    "apollo.participants.tasks.import_participants": _("Import Participants"),
    "apollo.submissions.tasks.init_submissions": _("Generate Checklists"),
    "apollo.users.tasks.import_users": _("Import Users"),
    "apollo.submissions.tasks.init_survey_submissions": _("Generate Surveys"),
}


def configure_image_storage(base_config: typing.Dict) -> None:
    """Configure the image storage backend."""
    # depots should only be configured once
    if not DepotManager.get("images"):
        configuration = base_config.copy()
        if settings.ATTACHMENTS_USE_S3:
            configuration.update(
                {
                    "depot.region_name": settings.AWS_IMAGES_REGION,
                    "depot.bucket": settings.AWS_IMAGES_BUCKET,
                }
            )
        else:
            configuration.update({"depot.storage_path": str(settings.IMAGE_UPLOAD_PATH)})

        DepotManager.configure("images", configuration)


def setup_attachment_storages() -> None:
    """Configure default upload storage backend."""
    if DepotManager.get() is None:
        base_config = {}
        if settings.ATTACHMENTS_USE_S3:
            base_config.update(
                {
                    "depot.backend": "depot.io.boto3.S3Storage",
                    "depot.access_key_id": settings.AWS_ACCESS_KEY_ID,
                    "depot.secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
                    "depot.region_name": settings.AWS_DEFAULT_REGION,
                    "depot.endpoint_url": settings.AWS_ENDPOINT_URL,
                    "depot.bucket": settings.AWS_DEFAULT_BUCKET,
                }
            )
        else:
            base_config.update(
                {
                    "depot.backend": "depot.io.local.LocalFileStorage",
                    "depot.storage_path": str(settings.BASE_UPLOAD_PATH),
                }
            )

        # TODO: configure default storage?
        configure_image_storage(base_config)


def create_app(package_name, package_path, settings_override=None, register_all_blueprints=True):
    """Returns a :class:`Flask` application instance configured with common functionality for the Overholt platform.

    :param package_name: application package name
    :param package_path: application package path
    :param settings_override: a dictionary of settings to override
    :param register_security_blueprint: flag to specify if the Flask-Security
                                        Blueprint should be registered.
                                        Defaults to `True`.
    """
    app = Flask(package_name, instance_relative_config=True)
    app.config.from_object("apollo.settings")
    app.config.from_object(settings_override)

    class ApolloMailUtil(MailUtil):
        def send_mail(self, template, subject, recipient, sender, body, html, **kwargs):
            from apollo.tasks import send_email

            send_email.delay(subject=subject, sender=sender, recipients=[recipient], body=body)

    def _before_send(event, hint):
        with app.app_context():
            if current_user and current_user.is_anonymous is False:
                deployment = current_user.deployment
                current_event = getattr(current_user, "event", None)
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
        auto_enabling_integrations=False,
        dsn=app.config.get("SENTRY_DSN"),
        debug=app.config.get("DEBUG"),
        release=app.config.get("VERSION"),
        send_default_pii=True,
        integrations=[
            FlaskIntegration(transaction_style="url"),
            CeleryIntegration(propagate_traces=True),
            SqlalchemyIntegration(),
        ],
        before_send=_before_send,
    )
    user_datastore = SQLAlchemyUserDatastore(db, models.User, models.Role)
    security.init_app(
        app,
        user_datastore,
        mail_util_cls=ApolloMailUtil,
        login_form=DeploymentLoginForm,
        register_blueprint=register_all_blueprints,
    )
    configure_uploads(app, uploads)

    # Prometheus Exporter
    if app.config.get("PROMETHEUS_SECRET"):
        metrics.path = f"/metrics/{app.config.get('PROMETHEUS_SECRET')}"
        metrics.init_app(app)
        try:
            metrics.info("app_info", "Apollo", version=app.config.get("COMMIT") or app.config.get("VERSION"))
        except ValueError:
            # ignore double registration of the metric
            pass

    # set up JWT callbacks
    jwt_manager.expired_token_loader(jwt_hooks.process_expired_token)
    jwt_manager.invalid_token_loader(jwt_hooks.process_invalid_token)
    jwt_manager.revoked_token_loader(jwt_hooks.process_revoked_token)
    jwt_manager.token_in_blocklist_loader(jwt_hooks.check_if_token_is_blocklisted)

    if app.config.get("PREFERRED_URL_SCHEME") == "https":
        SSLify(app)

    if app.config.get("DEBUG") and fdt_available:
        debug_toolbar.init_app(app)

    def get_locale():
        # get a list of available language codes,
        # starting from the current user's selected
        # language
        language_codes = set()
        if current_user and current_user.is_anonymous is False:
            if current_user.locale:
                return current_user.locale

        language_codes.update(app.config.get("LANGUAGES", {}).keys())

        if has_request_context():
            return request.accept_languages.best_match(language_codes)

    babel.init_app(app, locale_selector=get_locale)
    register_blueprints(app, package_name, package_path)

    if register_all_blueprints:
        menu.init_app(app)
        for configured_app in app.config.get("APPLICATIONS"):
            register_blueprints(app, configured_app, import_module(configured_app).__path__)

    # set up processing for attachments
    setup_attachment_storages()

    return app


def make_celery(app: Flask) -> Celery:
    """Initialize the celery application."""

    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery = Celery(app.name, task_cls=FlaskTask)
    celery.config_from_object(app.config["CELERY"])
    celery.set_default()
    app.extensions["celery"] = celery
    return celery
