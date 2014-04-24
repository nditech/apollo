# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from . import route, permissions
from flask import (Blueprint, render_template)
from flask.ext.babel import lazy_gettext as _
from flask.ext.menu import register_menu
from flask.ext.security import login_required

bp = Blueprint('forms', __name__, template_folder='templates',
               static_folder='static')


@route(bp, '/formbuilder')
@register_menu(
    bp, 'formbuilder', _('Form Builder'),
    visible_when=lambda: permissions.edit_forms.can())
@permissions.edit_forms.require(403)
@login_required
def index():
    page_title = _('Form Builder')
    template_name = 'frontend/formbuilder.html'

    ctx = dict(
        page_title=page_title
    )

    return render_template(template_name, **ctx)
