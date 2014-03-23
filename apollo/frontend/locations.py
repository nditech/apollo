# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from flask import Blueprint, g, redirect, render_template, request, url_for
from flask.ext.babel import lazy_gettext as _
from ..models import Location
from . import route
from .forms import generate_location_edit_form

bp = Blueprint('locations', __name__, template_folder='templates',
               static_folder='static', static_url_path='/core/static')


@route(bp, '/location/<pk>', methods=['GET', 'POST'])
def location_edit(pk):
    template_name = 'core/location_edit.html'
    deployment = g.get('deployment')
    location = Location.objects.get_or_404(pk=pk, deployment=deployment)
    page_title = _('Edit location: %(name)s', name=location.name)

    if request.method == 'GET':
        form = generate_location_edit_form(location)
    else:
        form = generate_location_edit_form(location, request.form)

        if form.validate():
            form.populate_obj(location)
            location.save()

            return redirect(url_for('core.location_list'))

    return render_template(template_name, form=form, page_title=page_title)
