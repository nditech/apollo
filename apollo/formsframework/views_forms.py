# -*- coding: utf-8 -*-
from io import BytesIO

from apollo.frontend import route, permissions
from flask import (
    abort, Blueprint, flash, g, redirect, render_template, request,
    send_file, url_for)
from flask_babelex import lazy_gettext as _
from flask_menu import register_menu
from flask_security import login_required
import json

from apollo import models, services
from apollo.formsframework.forms import FormForm, FormImportForm
from apollo.formsframework.models import FormBuilderSerializer
from apollo.formsframework import utils
from apollo.frontend.forms import make_checklist_init_form
from apollo.submissions.tasks import init_submissions
from apollo.utils import generate_identifier

bp = Blueprint('forms', __name__, template_folder='templates',
               static_folder='static')


@route(bp, '/forms/set/<int:form_set_id>/init',
       endpoint='checklist_init_with_set', methods=['POST'])
@route(bp, '/forms/init',
       endpoint='checklist_init', methods=['POST'])
@login_required
@permissions.edit_forms.require(403)
def checklist_init(form_set_id=0):
    if form_set_id:
        form_set = services.form_sets.fget_or_404(id=form_set_id)
    else:
        form_set = g.event.form_set or abort(400)

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

    if form_set_id:
        return redirect(url_for('.list_forms_with_set',
                                form_set_id=form_set.id))
    else:
        return redirect(url_for('.list_forms'))


@route(bp, '/formbuilder/set/<int:form_set_id>/form/<int:id>',
       endpoint='form_builder_with_set', methods=['GET', 'POST'])
@route(bp, '/formbuilder/<int:id>',
       endpoint='form_builder', methods=['GET', 'POST'])
@login_required
@permissions.edit_forms.require(403)
def form_builder(id, form_set_id=0):
    page_title = _('Form Builder')
    template_name = 'frontend/formbuilder.html'
    form = services.forms.fget_or_404(id=id)

    ctx = dict(
        page_title=page_title,
        form=form
    )

    if request.method == 'GET':
        ctx['form_set_id'] = form_set_id
        ctx['form_data'] = FormBuilderSerializer.serialize(form)
        return render_template(template_name, **ctx)
    else:
        data = request.get_json()

        if data:
            FormBuilderSerializer.deserialize(form, data)

        return ''


@route(bp, '/forms/set/<int:form_set_id>/new',
       endpoint='new_form_with_set', methods=['GET', 'POST'])
@route(bp, '/forms/new',
       endpoint='new_form', methods=['GET', 'POST'])
@login_required
@permissions.edit_forms.require(403)
def new_form(form_set_id=0):
    if form_set_id:
        form_set = services.form_sets.fget_or_404(id=form_set_id)
        template_name = 'frontend/form_edit_with_set.html'
    else:
        form_set = g.event.form_set or abort(404)
        template_name = 'frontend/form_edit.html'

    page_title = _('Create Form')

    web_form = FormForm()

    if not web_form.validate_on_submit():
        context = {
            'page_title': page_title,
            'form': web_form,
            'form_set_id': form_set_id,
            'form_set': form_set
        }

        return render_template(template_name, **context)

    # hack because of nasty bug with forms service
    form = services.forms.__model__(
        deployment_id=form_set.deployment_id,
        form_set_id=form_set.id)
    web_form.populate_obj(form)
    form.save()

    # add default role permissions for this form
    roles = models.Role.query.filter_by(
        deployment_id=form_set.deployment_id).all()
    form.roles = roles
    form.save()

    if form_set_id:
        return redirect(url_for('.list_forms_with_set',
                        form_set_id=form_set.id))
    else:
        return redirect(url_for('.list_forms'))


@route(bp, '/forms/set/<int:form_set_id>/form/<int:form_id>',
       endpoint='edit_form_with_set', methods=['GET', 'POST'])
@route(bp, '/forms/<int:form_id>',
       endpoint='edit_form', methods=['GET', 'POST'])
@login_required
@permissions.edit_forms.require(403)
def edit_form(form_id, form_set_id=0):
    if form_set_id:
        form_set = services.form_sets.fget_or_404(id=form_set_id)
        template_name = 'frontend/form_edit_with_set.html'
    else:
        form_set = g.event.form_set or abort(404)
        template_name = 'frontend/form_edit.html'

    form = services.forms.fget_or_404(id=form_id, form_set_id=form_set.id)
    page_title = _('Edit %(name)s', name=form.name)
    web_form = FormForm(obj=form)

    if not web_form.validate_on_submit():
        context = {
            'page_title': page_title,
            'form': web_form,
            'form_set_id': form_set_id,
            'form_set': form_set
        }

        return render_template(template_name, **context)

    web_form.populate_obj(form)
    form.save()

    if form_set_id:
        return redirect(url_for('.list_forms_with_set',
                        form_set_id=form_set_id))
    else:
        return redirect(url_for('.list_forms'))


@route(bp, '/forms', endpoint="list_forms", methods=['GET'])
@route(bp, '/forms/set/<int:form_set_id>',
       endpoint="list_forms_with_set", methods=['GET'])
@register_menu(
    bp, 'user.forms', _('Forms'),
    visible_when=lambda: permissions.edit_forms.can())
@login_required
@permissions.edit_forms.require(403)
def list_forms(form_set_id=0):
    if form_set_id:
        form_set = services.form_sets.fget_or_404(id=form_set_id)
        template_name = 'frontend/form_list_with_set.html'
    else:
        form_set = g.event.form_set or abort(404)
        template_name = 'frontend/form_list.html'

    page_title = _('Forms')

    forms = services.forms.find(form_set_id=form_set.id).order_by('name')
    checklist_init_form = make_checklist_init_form(g.event)
    form_import_form = FormImportForm()

    context = {
        'forms': forms,
        'page_title': page_title,
        'init_form': checklist_init_form,
        'form_import_form': form_import_form,
        'form_set': form_set
    }

    return render_template(template_name, **context)


@route(bp, '/forms/set/<int:form_set_id>/form/<int:form_id>/qa',
       endpoint='quality_assurance_with_set', methods=['GET', 'POST'])
@route(bp, '/forms/<int:form_id>/qa',
       endpoint='quality_assurance', methods=['GET', 'POST'])
@login_required
@permissions.edit_forms.require(403)
def quality_assurance(form_id, form_set_id=0):
    if form_set_id:
        form_set = services.form_sets.fget_or_404(id=form_set_id)
    else:
        form_set = g.event.form_set or abort(404)

    template_name = 'frontend/quality_assurance.html'
    form = services.forms.fget_or_404(id=form_id, form_set_id=form_set.id)
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

            if form_set_id:
                return redirect(url_for('.list_forms_with_set',
                                        form_set_id=form_set.id))
            else:
                return redirect(url_for('.list_forms'))
        except ValueError:
            pass

    check_data = [
        (c['description'], c['lvalue'], c['comparator'], c['rvalue'])
        for c in form.quality_checks
    ] if form.quality_checks else [[''] * 4]

    context = {
        'page_title': page_title,
        'check_data': check_data,
        'form_set': form_set,
        'form_set_id': form_set_id
    }

    return render_template(template_name, **context)


@route(bp, '/forms/<int:id>/export', methods=['GET'])
@login_required
@permissions.edit_forms.require(403)
def export_form(id):
    form = services.forms.fget_or_404(id=id)
    memory_file = BytesIO()
    workbook = utils.export_form(form)
    workbook.save(memory_file)
    memory_file.seek(0)
    filename = '{}.xls'.format(form.name)

    return send_file(
        memory_file, attachment_filename=filename, as_attachment=True,
        mimetype='application/vnd.ms-excel')


@route(bp, '/forms/set/<int:form_set_id>/import',
       endpoint='import_form_schema_with_set', methods=['POST'])
@route(bp, '/forms/import',
       endpoint='import_form_schema', methods=['POST'])
@login_required
@permissions.edit_forms.require(403)
def import_form_schema(form_set_id=0):
    if form_set_id:
        form_set = services.form_sets.fget_or_404(id=form_set_id)
    else:
        form_set = g.event.form_set or abort(404)

    web_form = FormImportForm()

    if web_form.validate_on_submit():
        form = utils.import_form(request.files['import_file'])
        form.deployment_id = form_set.deployment_id
        form.form_set = form_set
        form.save()

        # add default role permissions for this form
        roles = models.Role.query.filter_by(
            deployment_id=form_set.deployment_id).all()
        form.roles = roles
        form.save()

    if form_set_id:
        return redirect(url_for('.list_forms_with_set',
                        form_set_id=form_set.id))
    else:
        return redirect(url_for('.list_forms'))
