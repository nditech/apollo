# -*- coding: utf-8 -*-
from flask import (
    Blueprint, make_response, render_template, send_from_directory)
from flask_babelex import lazy_gettext as _

from apollo.frontend import route


blueprint = Blueprint('pwa', __name__, static_folder='static',
                      template_folder='templates', url_prefix='/pwa')


@route(blueprint, '/')
def index():
    context = {}
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
