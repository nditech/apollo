from functools import wraps


from flask import render_template, session, request, redirect, url_for
from flask.ext.login import user_logged_out
from flask.ext.mongoengine import MongoEngineSessionInterface
from flask.ext.principal import identity_loaded
from flask.ext.security import MongoEngineUserDatastore

from .. import factory, models, services
from ..core import db, menu, security, gravatar

from . import assets, permissions
from .helpers import set_request_presets
from . import template_filters


def create_app(settings_override=None, register_security_blueprint=True):
    """Returns the frontend application instance"""
    app = factory.create_app(__name__, __path__, settings_override)

    # Init assets
    assets.init_app(app)

    menu.init_app(app)
    gravatar.init_app(app)

    userdatastore = MongoEngineUserDatastore(db, models.User, models.Role)

    security.init_app(app, userdatastore,
                      register_blueprint=register_security_blueprint)
    app.session_interface = MongoEngineSessionInterface(db)

    # Register custom error handlers
    if not app.debug:
        for e in [500, 404, 403]:
            app.errorhandler(e)(handle_error)

    @app.before_first_request
    def create_user_roles():
        userdatastore.find_or_create_role('clerk')
        userdatastore.find_or_create_role('manager')
        userdatastore.find_or_create_role('analyst')
        userdatastore.find_or_create_role('admin')

        # permissions
        services.perms.get_or_create(action='view_events')
        services.perms.get_or_create(action='view_messages')
        services.perms.get_or_create(action='view_analyses')
        services.perms.get_or_create(action='send_messages')
        services.perms.get_or_create(action='edit_participant')
        services.perms.get_or_create(action='export_participants')
        services.perms.get_or_create(action='import_participants')
        services.perms.get_or_create(action='export_messages')

        services.perms.get_or_create(action='add_submission')
        services.perms.get_or_create(action='edit_submission')
        services.perms.get_or_create(action='export_submissions')

    # register deployment selection middleware
    app.before_request(set_request_presets)

    # add Jinja2 filters
    app.jinja_env.filters.update(
        checklist_question_summary=template_filters.checklist_question_summary
    )
    app.jinja_env.filters.update(
        get_location_for_type=template_filters.get_location_for_type
    )
    app.jinja_env.filters.update(pagelist=template_filters.gen_page_list)
    app.jinja_env.filters.update(percent_of=template_filters.percent_of)
    app.jinja_env.filters.update(timestamp=template_filters.mkunixtimestamp)

    # Login and logout signal handlers
    user_logged_out.connect(lambda app, user: session.clear())

    @identity_loaded.connect_via(app)
    def on_identity_loaded(sender, identity):
        needs = services.perms.get_all_needs(
            models.User(**identity.user._data))

        for need in needs:
            identity.provides.add(need)

    @app.context_processor
    def inject_permissions():
        return dict(perms=permissions)

    return app


def handle_error(e):
    code = getattr(e, 'code', 500)
    if code == 403:
        session['redirected_from'] = request.url
        return redirect(url_for('security.login'))
    else:
        return render_template('{code}.html'.format(code=code)), code


def route(bp, *args, **kwargs):
    def decorator(f):
        @bp.route(*args, **kwargs)
        @wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        return f

    return decorator
