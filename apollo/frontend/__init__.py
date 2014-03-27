from functools import wraps


from flask import render_template, session
from flask.ext.login import user_logged_out
from flask.ext.security import login_required

from .. import factory

from . import assets
from .helpers import gen_page_list, set_request_presets


def create_app(settings_override=None):
    """Returns the frontend application instance"""
    app = factory.create_app(__name__, __path__, settings_override)

    # Init assets
    assets.init_app(app)

    # Register custom error handlers
    if not app.debug:
        for e in [500, 404, 403]:
            app.errorhandler(e)(handle_error)

    # register deployment selection middleware
    app.before_request(set_request_presets)

    # add Jinja2 filters
    app.jinja_env.filters.update(pagelist=gen_page_list)

    # Login and logout signal handlers
    user_logged_out.connect(lambda app, user: session.clear())

    return app


def handle_error(e):
    code = getattr(e, 'code', 500)
    return render_template('{code}.html'.format(code=code)), code


def route(bp, *args, **kwargs):
    def decorator(f):
        @bp.route(*args, **kwargs)
        @login_required
        @wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        return f

    return decorator
