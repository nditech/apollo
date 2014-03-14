from flask import Blueprint, render_template, url_for, current_app as app

core = Blueprint('core', __name__, template_folder='templates',
                 static_folder='static', static_url_path='/core/static')


@core.app_errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403


@core.app_errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@core.app_errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


@core.route('/')
def index():
    return 'Hello, world!'
