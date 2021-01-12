# -*- coding: utf-8 -*-
from flask import Blueprint, render_template

from apollo.frontend import route

bp = Blueprint('pwa', __name__, static_folder='static',
               template_folder='templates', url_prefix='/pwa')


@route(bp, '/')
def index():
    template_name = 'pwa/index.html'

    return render_template(template_name)


@route(bp, '/login')
def login():
    template_name = 'pwa/login.html'

    return render_template(template_name)
