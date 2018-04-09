# -*- coding: utf-8 -*-
from io import BytesIO

from apollo.frontend import route, permissions
from flask import (
    Blueprint, current_app, flash, g, redirect, render_template, request,
    send_file, url_for)
from flask_babelex import lazy_gettext as _
from flask_menu import register_menu
from flask_security import login_required
import json

from apollo import services
from apollo.formsframework.forms import FormForm, FormImportForm
from apollo.formsframework.models import FormBuilderSerializer, import_form
from apollo.submissions.tasks import init_submissions
from apollo.frontend.forms import make_checklist_init_form

bp = Blueprint('forms', __name__, template_folder='templates',
               static_folder='static')


@route(bp, '/form-sets', methods=['GET'])
@permissions.edit_forms.require(403)
def form_set_list():
    args = request.args.to_dict(flat=False)
    page_title = _('Form sets')
    queryset = services.form_sets.find(deployment=g.deployment)
    template_name = 'frontend/form_set_list.html'

    page_spec = args.pop('page', [1])
    try:
        page = int(page_spec[0])
    except (IndexError, ValueError):
        page = 1

    context = {
        'form_sets': queryset.paginate(
            page=page, per_page=current_app.config.get('PAGE_SIZE')),
        'page_title': page_title
    }

    return render_template(template_name, **context)


@route(bp, '/forms/set/<int:form_set_id>/init', methods=['POST'])
@permissions.edit_forms.require(403)
@login_required
def checklist_init(form_set_id):
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

    return redirect(url_for('.list_forms', form_set_id=form_set_id))


@route(bp, '/formbuilder/<int:id>', methods=['GET', 'POST'])
@permissions.edit_forms.require(403)
@login_required
def form_builder(id):
    page_title = _('Form Builder')
    template_name = 'frontend/formbuilder.html'
    form = services.forms.fget_or_404(id=id)

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


@route(bp, '/forms/set/<int:form_set_id>/new', methods=['GET', 'POST'])
@permissions.edit_forms.require(403)
@login_required
def new_form(form_set_id):
    form_set = services.form_sets.fget_or_404(id=form_set_id)
    page_title = _('Create form')
    template_name = 'frontend/form_edit.html'

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
        form_set_id=form_set_id)
    web_form.populate_obj(form)
    form.save()

    return redirect(url_for('.list_forms', form_set_id=form_set_id))


@route(bp, '/forms/set/<int:form_set_id>/<int:form_id>',
       methods=['GET', 'POST'])
@permissions.edit_forms.require(403)
@login_required
def edit_form(form_set_id, form_id):
    form_set = services.forms.fget_or_404(id=form_set_id)
    form = services.forms.fget_or_404(id=form_id, form_set_id=form_set_id)
    page_title = _('Edit %(name)s', name=form.name)
    template_name = 'frontend/form_edit.html'

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

    return redirect(url_for('.list_forms', form_set_id=form_set_id))


@route(bp, '/forms/set/<int:form_set_id>')
@register_menu(
    bp, 'user.forms', _('Forms'),
    visible_when=lambda: permissions.edit_forms.can())
@permissions.edit_forms.require(403)
@login_required
def list_forms(form_set_id):
    page_title = _('Forms')
    template_name = 'frontend/form_list.html'
    forms = services.forms.find(form_set_id=form_set_id)
    form_set = services.form_sets.fget_or_404(id=form_set_id)
    checklist_init_form = make_checklist_init_form(g.event)
    form_import_form = FormImportForm()

    context = {
        'form_set_id': form_set_id,
        'forms': forms,
        'page_title': page_title,
        'init_form': checklist_init_form,
        'form_import_form': form_import_form,
        'form_set': form_set
    }

    return render_template(template_name, **context)


@route(bp, '/forms/set/<int:form_set_id>/<int:form_id>/qa',
       methods=['GET', 'POST'])
@permissions.edit_forms.require(403)
@login_required
def quality_assurance(form_set_id, form_id):
    form_set = services.form_sets.fget_or_404(id=form_set_id)
    form = services.forms.fget_or_404(id=form_id, form_set_id=form_set_id)
    page_title = _('Quality Assurance — %(name)s', name=form.name)
    template_name = 'frontend/quality_assurance.html'

    if request.method == 'POST':
        try:
            postdata = json.loads(request.form.get('postdata'))
            form.quality_checks = []
            for item in postdata:
                if isinstance(item, list):
                    (name, desc, lhs, comp, rhs) = item
                elif isinstance(item, dict):
                    name = item["0"]
                    desc = item["1"]
                    lhs = item["2"]
                    comp = item["3"]
                    rhs = item["4"]

                if name and desc and lhs and comp and rhs:
                    form.quality_checks.append({
                        'name': name, 'description': desc,
                        'lvalue': lhs, 'comparator': comp,
                        'rvalue': rhs
                    })
            form.save()
            return redirect(url_for('.list_forms', form_set_id=form_set_id))
        except ValueError:
            pass

    check_data = [
        (c['name'],
         c['description'], c['lvalue'], c['comparator'], c['rvalue'])
        for c in form.quality_checks
    ] if form.quality_checks else [[''] * 5]

    context = {
        'page_title': page_title,
        'check_data': check_data,
        'form_set': form_set
    }

    return render_template(template_name, **context)


@route(bp, '/forms/<int:id>/export', methods=['GET'])
@permissions.edit_forms.require(403)
@login_required
def export_form(id):
    form = services.forms.fget_or_404(id=id)
    memory_file = BytesIO()
    workbook = form.to_excel()
    workbook.save(memory_file)
    memory_file.seek(0)
    filename = '{}.xls'.format(form.name)

    return send_file(
        memory_file, attachment_filename=filename, as_attachment=True,
        mimetype='application/vnd.ms-excel')


@route(bp, '/forms/set/<int:form_set_id>/import', methods=['POST'])
@permissions.edit_forms.require(403)
@login_required
def import_form_schema(form_set_id):
    form_set = services.form_sets.fget_or_404(id=form_set_id)
    web_form = FormImportForm()

    if web_form.validate_on_submit():
        form = import_form(request.files['import_file'])
        form.deployment_id = form_set.deployment_id
        form.form_set = form_set
        form.save()

    return redirect(url_for('.list_forms', form_set_id=form_set_id))
