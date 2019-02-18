# -*- coding: utf-8 -*-
from flask import g, render_template, session, request, redirect, url_for
from flask_admin import AdminIndexView
from flask_login import user_logged_out
from flask_principal import identity_loaded
from flask_security import SQLAlchemyUserDatastore, current_user
from whitenoise import WhiteNoise
from apollo import assets, models, services

from apollo.frontend import permissions, template_filters
from apollo.core import admin, db, menu, security, gravatar, csrf, webpack
from apollo.prometheus.flask import monitor
from .frontend.helpers import set_request_presets
from .security_ext_forms import DeploymentLoginForm

from apollo import factory

custom_filters = {
    'checklist_question_summary': template_filters.checklist_question_summary,
    'get_location_for_type': template_filters.get_location_for_type,
    'pagelist': template_filters.gen_page_list,
    'percent_of': template_filters.percent_of,
    'timestamp': template_filters.mkunixtimestamp,
    'mean_filter': template_filters.mean_filter,
    'reverse_dict': template_filters.reverse_dict,
    'qa_status': template_filters.qa_status,
}


def init_admin(admin, app):
    class AdminIndex(AdminIndexView):
        def is_accessible(self):
            return current_user.is_admin()

    admin.init_app(app)
    admin.index_view = AdminIndex()


def create_app(settings_override=None, register_security_blueprint=True):
    """Returns the frontend application instance"""
    app = factory.create_app(__name__, __path__, settings_override)

    app.wsgi_app = WhiteNoise(app.wsgi_app, root='static/')

    # Init assets
    assets.init_app(app)
    webpack.init_app(app)

    menu.init_app(app)
    gravatar.init_app(app)

    userdatastore = SQLAlchemyUserDatastore(db, models.User, models.Role)

    security.init_app(app, userdatastore,
                      login_form=DeploymentLoginForm,
                      register_blueprint=register_security_blueprint)

    csrf.init_app(app)
    init_admin(admin, app)

    monitor(app)

    # Register custom error handlers
    if not app.debug:
        for e in [500, 404, 403]:
            app.errorhandler(e)(handle_error)

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
        ga_key = app.config.get('GOOGLE_ANALYTICS_KEY')
        gtm_key = app.config.get('GOOGLE_TAG_MANAGER_KEY')
        return dict(perms=permissions, ga_key=ga_key, gtm_key=gtm_key)

    # clickjacking protection
    @app.after_request
    def frame_buster(response):
        response.headers['X-Frame-Options'] = app.config.get(
            'X_FRAME_OPTIONS', 'DENY')
        return response

    # content security policy
    @app.after_request
    def content_security_policy(response):
        response.headers['Content-Security-Policy'] = "default-src 'self' " + \
            "*.googlecode.com *.google-analytics.com " + \
            "*.googletagmanager.com " + \
            "cdn.heapanalytics.com heapanalytics.com " + \
            "fontlibrary.org " + \
            "'unsafe-inline' 'unsafe-eval' data:; img-src * data:"
        return response

    return app


def clear_session(app, user):
    # clear session
    session.clear()

    # pop request globals
    delattr(g, 'deployment')
    delattr(g, 'event')
    delattr(g, 'locale')


def handle_error(e):
    code = getattr(e, 'code', 500)
    if code == 403:
        session['redirected_from'] = request.url
        return redirect(url_for('security.login'))
    else:
        return render_template('{code}.html'.format(code=code)), code
