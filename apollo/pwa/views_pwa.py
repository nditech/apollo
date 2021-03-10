# -*- coding: utf-8 -*-
from configparser import ConfigParser, Error
from pathlib import Path

from flask import (
    Blueprint, jsonify, make_response, render_template, send_from_directory)
from flask_babelex import lazy_gettext as _

from apollo import settings
from apollo.frontend import route


blueprint = Blueprint('pwa', __name__, static_folder='static',
                      template_folder='templates', url_prefix='/pwa')


@route(blueprint, '/')
def index():
    version_file_path = Path(settings.PROJECT_ROOT).joinpath('version.ini')
    if version_file_path.exists():
        parser = ConfigParser()
        parser.read([version_file_path])

        try:
            commit = parser.get('settings', 'commit')
        except Error:
            commit = 'unknown'
    else:
        commit = 'unknown'

    context = {'commit': commit}
    page_title = _('Apollo')
    template_name = 'pwa/index.html'

    context['page_title'] = page_title

    return render_template(template_name, **context)


@route(blueprint, '/serviceworker.js')
def service_worker():
    response = make_response(send_from_directory(
        blueprint.static_folder, filename='js/serviceworker.js'))
    response.headers['Content-Type'] = 'application/javascript'
    return response


@route(blueprint, '/versioncheck')
def version_check():
    version_file_path = Path(settings.PROJECT_ROOT).joinpath('version.ini')
    if version_file_path.exists():
        parser = ConfigParser()
        parser.read([version_file_path])

        try:
            version_info = dict(parser['settings'])

            return jsonify(version_info)
        except (KeyError, TypeError):
            pass

    return jsonify({'version': 'unknown', 'commit': 'unknown'})
