# -*- coding: utf-8 -*-
from io import BytesIO

from apollo.frontend import route, permissions
from flask import (
    Blueprint, flash, g, redirect, render_template, request,
    send_file, url_for)
from flask_babelex import lazy_gettext as _
from flask_menu import register_menu
from flask_security import login_required
import json

from apollo import models
from apollo.formsframework.forms import FormForm, FormImportForm
from apollo.formsframework.models import FormBuilderSerializer
from apollo.formsframework import utils
from apollo.frontend.forms import make_checklist_init_form
from apollo.submissions.tasks import init_submissions
from apollo.utils import generate_identifier

bp = Blueprint('forms', __name__, template_folder='templates',
               static_folder='static')


@route(bp, '/forms/init',
       endpoint='checklist_init', methods=['POST'])
@login_required
@permissions.edit_forms.require(403)
def checklist_init():
    flash_message = ''
    flash_category = ''
    form = make_checklist_init_form(g.event)

    if form.validate_on_submit():
        flash_category = 'checklist_init_success'
        flash_message = _('Checklists are being created for the form, '
                          'role and location type you selected in the '
                          'current event')

        init_submissions.delay(
            g.event.id,
            form.data['form'],
            form.data['role'],
            form.data['location_type'])
    else:
        flash_category = 'checklist_init_failure'
        flash_message = _('Checklists were not created')

    flash(str(flash_message), flash_category)
    return redirect(url_for('.list_forms'))


@route(bp, '/formbuilder/<int:id>',
       endpoint='form_builder', methods=['GET', 'POST'])
@login_required
@permissions.edit_forms.require(403)
def form_builder(id):
    page_title = _('Form Builder')
    template_name = 'frontend/formbuilder.html'
    form = models.Form.query.filter_by(id=id).first_or_404()

    ctx = dict(
        page_title=page_title,
        form=form
    )

    if request.method == 'GET':
        ctx['form_data'] = FormBuilderSerializer.serialize(form)
        return render_template(template_name, **ctx)
    else:
        data = request.get_json()

        if data:
            FormBuilderSerializer.deserialize(form, data)

        return ''


@route(bp, '/form/new',
       endpoint='new_form', methods=['GET', 'POST'])
@login_required
@permissions.edit_forms.require(403)
def new_form():
    template_name = 'frontend/form_edit.html'

    page_title = _('Create Form')

    web_form = FormForm()

    if not web_form.validate_on_submit():
        context = {
            'page_title': page_title,
            'form': web_form
        }

        return render_template(template_name, **context)

    form = models.Form(deployment_id=g.event.deployment_id)
    web_form.populate_obj(form)
    form.save()

    # add default role permissions for this form
    roles = models.Role.query.filter_by(
        deployment_id=g.event.deployment_id).all()
    form.roles = roles
    form.save()

    return redirect(url_for('.list_forms'))


@route(bp, '/form/<int:form_id>',
       endpoint='edit_form', methods=['GET', 'POST'])
@login_required
@permissions.edit_forms.require(403)
def edit_form(form_id):
    template_name = 'frontend/form_edit.html'

    form = models.Form.query.filter_by(id=form_id).first_or_404()
    page_title = _('Edit %(name)s', name=form.name)
    web_form = FormForm(obj=form)

    if not web_form.validate_on_submit():
        context = {
            'page_title': page_title,
            'form': web_form,
        }

        return render_template(template_name, **context)

    web_form.populate_obj(form)
    form.save()

    return redirect(url_for('.list_forms'))


@route(bp, '/forms', endpoint="list_forms", methods=['GET'])
@register_menu(
    bp, 'user.forms', _('Forms'),
    visible_when=lambda: permissions.edit_forms.can())
@login_required
@permissions.edit_forms.require(403)
def list_forms():
    template_name = 'frontend/form_list.html'

    page_title = _('Forms')

    forms = models.Form.query.order_by('name').all()
    checklist_init_form = make_checklist_init_form(g.event)
    form_import_form = FormImportForm()

    context = {
        'forms': forms,
        'page_title': page_title,
        'init_form': checklist_init_form,
        'form_import_form': form_import_form,
    }

    return render_template(template_name, **context)


@route(bp, '/form/<int:form_id>/qa',
       endpoint='quality_assurance', methods=['GET', 'POST'])
@login_required
@permissions.edit_forms.require(403)
def quality_assurance(form_id):
    template_name = 'frontend/quality_assurance.html'
    form = models.Form.query.filter_by(id=form_id).first_or_404()
    page_title = _('Quality Assurance — %(name)s', name=form.name)

    if request.method == 'POST':
        try:
            postdata = json.loads(request.form.get('postdata'))
            form.quality_checks = []
            for item in postdata:
                if isinstance(item, list):
                    desc = item[0]
                    lhs = item[1]
                    comp = item[2]
                    rhs = item[3]
                elif isinstance(item, dict):
                    desc = item["0"]
                    lhs = item["1"]
                    comp = item["2"]
                    rhs = item["3"]

                if desc and lhs and comp and rhs:
                    form.quality_checks.append({
                        'name': generate_identifier(), 'description': desc,
                        'lvalue': lhs, 'comparator': comp,
                        'rvalue': rhs
                    })
            form.save()

            return redirect(url_for('.list_forms'))
        except ValueError:
            pass

    check_data = [
        (c['description'], c['lvalue'], c['comparator'], c['rvalue'])
        for c in form.quality_checks
    ] if form.quality_checks else [[''] * 4]

    context = {
        'page_title': page_title,
        'check_data': check_data
    }

    return render_template(template_name, **context)


@route(bp, '/form/<int:id>/export', methods=['GET'])
@login_required
@permissions.edit_forms.require(403)
def export_form(id):
    form = models.Form.query.filter_by(id=id).first_or_404()
    memory_file = BytesIO()
    workbook = utils.export_form(form)
    workbook.save(memory_file)
    memory_file.seek(0)
    filename = '{}.xls'.format(form.name)

    return send_file(
        memory_file, attachment_filename=filename, as_attachment=True,
        mimetype='application/vnd.ms-excel')


@route(bp, '/forms/import',
       endpoint='import_form_schema', methods=['POST'])
@login_required
@permissions.edit_forms.require(403)
def import_form_schema():
    web_form = FormImportForm()

    if web_form.validate_on_submit():
        form = utils.import_form(request.files['import_file'])
        form.deployment_id = g.event.deployment_id
        form.save()

        # add default role permissions for this form
        roles = models.Role.query.filter_by(
            deployment_id=g.event.deployment_id).all()
        form.roles = roles
        form.save()

    return redirect(url_for('.list_forms'))
