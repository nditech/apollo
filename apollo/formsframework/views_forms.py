# -*- coding: utf-8 -*-
from __future__ import absolute_import
from apollo.frontend import route, permissions
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for)
from flask.ext.babel import lazy_gettext as _
from flask.ext.menu import register_menu
from flask.ext.security import login_required
import json

from apollo import services
from apollo.formsframework.forms import FormForm
from apollo.formsframework.models import FormBuilderSerializer
from apollo.formsframework.tasks import update_submissions
from apollo.submissions.tasks import init_submissions
from apollo.frontend.forms import ChecklistInitForm

bp = Blueprint('forms', __name__, template_folder='templates',
               static_folder='static')


@route(bp, '/forms/init', methods=['POST'])
@permissions.edit_forms.require(403)
@login_required
def checklist_init():
    flash_message = ''
    flash_category = ''
    form = ChecklistInitForm()

    try:
        str_func = unicode
    except NameError:
        str_func = str

    if form.validate_on_submit():
        flash_category = 'checklist_init_success'
        flash_message = _('Checklists are being created for the form, role and location type you selected in the current event')

        init_submissions.delay(
            str(g.deployment.pk),
            str(g.event.pk),
            form.data['form'],
            form.data['role'],
            form.data['location_type'])
    else:
        flash_category = 'checklist_init_failure'
        flash_message = _('Checklists were not created')

    flash(str_func(flash_message), flash_category)

    return redirect(url_for('.list_forms'))


@route(bp, '/formbuilder/<pk>', methods=['GET', 'POST'])
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
            update_submissions.delay(str(form.pk))

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
    bp, 'user.forms', _('Forms'),
    visible_when=lambda: permissions.edit_forms.can())
@permissions.edit_forms.require(403)
@login_required
def list_forms():
    page_title = _('Forms')
    template_name = 'frontend/form_list.html'
    forms = services.forms.find()
    checklist_init_form = ChecklistInitForm()

    context = {
        'forms': forms,
        'page_title': page_title,
        'init_form': checklist_init_form
    }

    return render_template(template_name, **context)


@route(bp, '/forms/<pk>/qa', methods=['GET', 'POST'])
@permissions.edit_forms.require(403)
@login_required
def quality_assurance(pk):
    form = services.forms.get_or_404(pk=pk)
    page_title = _(u'Quality Assurance — %(name)s', name=form.name)
    template_name = 'frontend/quality_assurance.html'

    if request.method == 'POST':
        try:
            postdata = json.loads(request.form.get('postdata'))
            form.quality_checks = []
            for (name, desc, lhs, comp, rhs) in postdata:
                if name and desc and lhs and comp and rhs:
                    form.quality_checks.append({
                        'name': name, 'description': desc,
                        'lvalue': lhs, 'comparator': comp,
                        'rvalue': rhs
                    })
            form.save()
            return redirect(url_for('.list_forms'))
        except ValueError:
            pass

    check_data = [
        (c['name'],
         c['description'], c['lvalue'], c['comparator'], c['rvalue'])
        for c in form.quality_checks
    ]

    context = {
        'page_title': page_title,
        'check_data': check_data
    }

    return render_template(template_name, **context)
