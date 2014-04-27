# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from flask import (
    Blueprint, g, redirect, render_template, request, url_for, flash
)
from flask.ext.babel import lazy_gettext as _
from flask.ext.security import login_required
from flask.ext.menu import register_menu
from ..models import Location
from . import route, permissions
from .forms import generate_location_edit_form

bp = Blueprint('locations', __name__, template_folder='templates',
               static_folder='static', static_url_path='/core/static')


@route(bp, '/location/<pk>', methods=['GET', 'POST'])
@register_menu(
    bp, 'edit_location', _('Edit Location'),
    visible_when=lambda: permissions.edit_locations.can())
@permissions.edit_locations.require(403)
@login_required
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


@route(bp, '/locations/builder', methods=['GET', 'POST'])
@register_menu(
    bp, 'locations_builder', _('Administrative Divisions'),
    visible_when=lambda: permissions.edit_locations.can())
@permissions.edit_locations.require(403)
@login_required
def locations_builder():
    template_name = 'frontend/location_builder.html'
    page_title = _('Administrative Divisions')

    if request.method == 'POST' and request.form.get('divisions_graph'):
        divisions_graph = request.form.get('divisions_graph')
        g.deployment.administrative_divisions_graph = divisions_graph
        g.deployment.save()
        g.deployment.reload()

        flash(
            _('Your changes have been saved.'),
            category='locations_builder'
        )

    return render_template(template_name, page_title=page_title)
