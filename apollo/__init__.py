# -*- coding: utf-8 -*-
"""Apollo root module."""

from datetime import datetime, timedelta
from urllib.parse import urlencode, urlparse

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask import g, redirect, render_template, request, session, url_for
from flask_admin import AdminIndexView
from flask_jwt_extended import (
    create_access_token,
    get_jwt,
    get_jwt_identity,
    set_access_cookies,
)
from flask_login import user_logged_out
from flask_principal import identity_loaded
from flask_security import current_user
from flask_security.utils import login_user, url_for_security
from loginpass import Facebook, Google, create_flask_blueprint
from whitenoise import WhiteNoise

from apollo import assets, factory, models, services, settings, utils
from apollo.cli import users_cli
from apollo.core import admin, csrf, docs, oauth, webpack
from apollo.frontend import permissions, template_filters

from .frontend.helpers import set_request_presets

custom_filters = {
    "checklist_question_summary": template_filters.checklist_question_summary,
    "get_location_for_type": template_filters.get_location_for_type,
    "pagelist": template_filters.gen_page_list,
    "percent_of": template_filters.percent_of,
    "timestamp": template_filters.mkunixtimestamp,
    "mean_filter": template_filters.mean_filter,
    "reverse_dict": template_filters.reverse_dict,
    "qa_status": template_filters.qa_status,
    "longitude": template_filters.longitude,
    "latitude": template_filters.latitude,
}


def init_admin(admin, app):
    """Initialize flask-admin."""

    class AdminIndex(AdminIndexView):
        def is_accessible(self):
            return current_user.is_admin()

    admin.init_app(app)
    admin.index_view = AdminIndex()


def create_app(settings_override=None):
    """Returns the frontend application instance."""
    # TODO: refactor out the need to use a factory
    app = factory.create_app(__name__, __path__, settings_override)

    app.wsgi_app = WhiteNoise(app.wsgi_app, root=app.static_folder, prefix="static/")

    # Init assets
    assets.init_app(app)
    webpack.init_app(app)

    oauth.init_app(app)

    # initialize the OpenAPI extension
    spec = APISpec(title="Apollo", version="1.0.0", openapi_version="3.0.2", plugins=[MarshmallowPlugin()])
    app.config.update({"APISPEC_SPEC": spec})
    docs.init_app(app)

    csrf.init_app(app)
    init_admin(admin, app)
    app.cli.add_command(users_cli)

    # Register custom error handlers
    if not app.debug:
        for e in [500, 404, 403]:
            app.register_error_handler(e, handle_error)

    # register deployment selection middleware
    app.before_request(set_request_presets)

    # add Jinja2 filters
    app.jinja_env.filters.update(custom_filters)

    # Login and logout signal handlers
    user_logged_out.connect(clear_session)

    @identity_loaded.connect_via(app)
    def on_identity_loaded(sender, identity):
        if current_user.is_authenticated:
            user = current_user._get_current_object()
            needs = services.users.get_permissions_cache(user)

            for need in needs:
                identity.provides.add(need)

    @app.context_processor
    def inject_permissions():
        ga_key = app.config.get("GOOGLE_ANALYTICS_KEY")
        gtm_key = app.config.get("GOOGLE_TAG_MANAGER_KEY")
        return {"perms": permissions, "ga_key": ga_key, "gtm_key": gtm_key}

    # clickjacking protection
    @app.after_request
    def frame_buster(response):
        response.headers["X-Frame-Options"] = app.config.get("X_FRAME_OPTIONS", "DENY")
        return response

    # content security policy
    @app.after_request
    def content_security_policy(response):
        sentry_dsn = settings.SENTRY_DSN or ""
        sentry_host = urlparse(sentry_dsn).netloc.split("@")[-1]
        response.headers["Content-Security-Policy"] = (
            "default-src 'self' blob: "
            + "*.googlecode.com *.google-analytics.com fonts.gstatic.com fonts.googleapis.com "
            + "*.googletagmanager.com "
            + "cdn.heapanalytics.com heapanalytics.com "
            + "'unsafe-inline' 'unsafe-eval' data:; img-src * data: blob:; "
            + f"connect-src 'self' {sentry_host}; "
        )
        return response

    # automatic token refresh
    @app.after_request
    def refresh_expiring_jwts(response):
        try:
            expiration_timestamp = get_jwt()["exp"]
            now = utils.current_timestamp()
            target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
            if target_timestamp > expiration_timestamp:
                access_token = create_access_token(identity=get_jwt_identity())
                set_access_cookies(response, access_token)

            return response
        except (KeyError, RuntimeError):
            return response

    def handle_authorize(remote, token, user_info):
        if user_info and "email" in user_info:
            user = models.User.query.filter_by(email=user_info["email"]).first()
            if user:
                login_user(user)
                return redirect(app.config.get("SECURITY_POST_LOGIN_VIEW"))

        return redirect(url_for_security("login"))

    @app.template_global()
    def modify_query(**values):
        args = request.args.copy()

        for k, v in values.items():
            if not v:
                _ = args.pop(k, None)
            else:
                args[k] = v

        return "{}?{}".format(request.path, urlencode(args))

    if app.config.get("ENABLE_SOCIAL_LOGIN", False):
        bp = create_flask_blueprint([Facebook, Google], oauth, handle_authorize)
        app.register_blueprint(bp, url_prefix="/social")

    celery = factory.make_celery(app)

    return app, celery


def clear_session(app, user):
    """Clears the session."""
    session.clear()

    # pop request globals
    delattr(g, "deployment")
    delattr(g, "event")
    delattr(g, "locale")


def handle_error(e):
    """Error handler."""
    code = getattr(e, "code", 500)
    if code == 403:
        session["redirected_from"] = request.url
        return redirect(url_for("security.login"))
    elif code == 404:
        return render_template("404.html"), code
    else:
        return render_template("500.html"), 500
