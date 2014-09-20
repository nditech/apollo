# -*- coding: utf-8 -*-
from __future__ import absolute_import
from . import route, permissions
from flask import (Blueprint, g, redirect, render_template, request, url_for)
from flask.ext.babel import lazy_gettext as _
from flask.ext.menu import register_menu
from flask.ext.security import login_required

from .. import services
from ..formsframework.forms import FormForm
from ..formsframework.models import FormBuilderSerializer

bp = Blueprint('forms', __name__, template_folder='templates',
               static_folder='static')


@route(bp, '/formbuilder/<pk>', methods=['GET', 'POST'])
@register_menu(
    bp, 'formbuilder', _('Form Builder'),
    visible_when=lambda: permissions.edit_forms.can())
@permissions.edit_forms.require(403)
@login_required
def form_builder(pk):
    page_title = _('Form Builder')
    template_name = 'frontend/formbuilder.html'
    form = services.forms.get_or_404(pk=pk)

    ctx = dict(
        page_title=page_title,
        form=form.name
    )

    if request.method == 'GET':
        ctx['form_data'] = FormBuilderSerializer.serialize(form)
        return render_template(template_name, **ctx)
    else:
        data = request.get_json()

        if data:
            FormBuilderSerializer.deserialize(form, data)

        return ''


@route(bp, '/forms/new', methods=['GET', 'POST'])
@permissions.edit_forms.require(403)
@login_required
def new_form():
    page_title = _('Create form')
    template_name = 'frontend/form_edit.html'

    web_form = FormForm()

    if not web_form.validate_on_submit():
        context = {
            'page_title': page_title,
            'form': web_form
        }

        return render_template(template_name, **context)

    deployment = g.get('deployment')
    event = g.get('event')

    # hack because of nasty bug with forms service
    form = services.forms.__model__(deployment=deployment, events=[event])
    web_form.populate_obj(form)
    form.save()

    return redirect(url_for('.list_forms'))


@route(bp, '/forms/<pk>', methods=['GET', 'POST'])
@permissions.edit_forms.require(403)
@login_required
def edit_form(pk):
    form = services.forms.get_or_404(pk=pk)
    page_title = _('Edit %(name)s', name=form.name)
    template_name = 'frontend/form_edit.html'

    web_form = FormForm(obj=form)

    if not web_form.validate_on_submit():
        context = {
            'page_title': page_title,
            'form': web_form
        }

        return render_template(template_name, **context)

    web_form.populate_obj(form)
    form.save()

    return redirect(url_for('.list_forms'))


@route(bp, '/forms')
@register_menu(
    bp, 'forms', _('Forms'),
    visible_when=lambda: permissions.edit_forms.can())
@permissions.edit_forms.require(403)
@login_required
def list_forms():
    page_title = _('Forms')
    template_name = 'frontend/form_list.html'
    forms = services.forms.find()

    context = {
        'forms': forms,
        'page_title': page_title
    }

    return render_template(template_name, **context)
