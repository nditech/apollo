from functools import wraps
from urlparse import urlparse

from flask import abort, g, render_template, request, session
from flask.ext.login import user_logged_in, user_logged_out
from flask.ext.security import login_required

from .. import factory
from ..models import Deployment
from . import assets
from .helpers import gen_page_list, select_default_event


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
    app.before_request(select_deployment)

    # add Jinja2 filters
    app.jinja_env.filters.update(pagelist=gen_page_list)

    # Login and logout signal handlers
    user_logged_in.connect(select_default_event)
    user_logged_out.connect(lambda app, user: session.clear())

    return app


def handle_error(e):
    return render_template('{errorcode}.html'.format(errorcode=e.code)), e.code


def select_deployment():
    hostname = urlparse(request.url).hostname

    try:
        g.deployment = Deployment.objects(hostnames=hostname).first()
    except Deployment.DoesNotExist:
        abort(404)


def route(bp, *args, **kwargs):
    def decorator(f):
        @bp.route(*args, **kwargs)
        @login_required
        @wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        return f

    return decorator
