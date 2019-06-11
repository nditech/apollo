# -*- coding: utf-8 -*-
from io import BytesIO

from flask import (
    Blueprint, flash, g, redirect, request,
    send_file, url_for)
from flask_babelex import lazy_gettext as _
import json

from apollo import core, models
from apollo.formsframework.forms import FormForm, FormImportForm
from apollo.formsframework.models import FormBuilderSerializer
from apollo.formsframework import utils
from apollo.formsframework.api import views as api_views
from apollo.frontend.forms import make_checklist_init_form
from apollo.submissions.tasks import init_submissions
from apollo.utils import generate_identifier

bp = Blueprint('forms', __name__, template_folder='templates',
               static_folder='static')

bp.add_url_rule(
    '/api/forms',
    view_func=api_views.FormListResource.as_view('api_form_list'))
bp.add_url_rule(
    '/api/forms/<int:form_id>',
    view_func=api_views.FormItemResource.as_view('api_form_item'))

core.docs.register(api_views.FormItemResource, 'forms.api_form_item')
core.docs.register(api_views.FormListResource, 'forms.api_form_list')


def checklist_init():
    flash_message = ''
    flash_category = ''
    form = make_checklist_init_form(g.event)

    if form.validate_on_submit():
        flash_category = 'info'
        flash_message = _('Checklists are being created for the form, '
                          'role and location type you selected in the '
                          'current event')

        init_submissions.delay(
            g.event.id,
            form.data['form'],
            form.data['role'],
            form.data['location_type'])
    else:
        flash_category = 'danger'
        flash_message = _('Checklists were not created')

    flash(str(flash_message), flash_category)
    return redirect(url_for('formsview.index'))


def form_builder(view, id):
    template_name = 'admin/formbuilder.html'
    form = models.Form.query.filter_by(id=id).first_or_404()
    breadcrumbs = [
        {'text': _('Forms'), 'url': url_for('formsview.index')},
        _('Form Builder'), form.name]

    ctx = dict(
        breadcrumbs=breadcrumbs,
        form=form
    )

    if request.method == 'GET':
        ctx['form_data'] = FormBuilderSerializer.serialize(form)
        return view.render(template_name, **ctx)
    else:
        data = request.get_json()

        if data:
            FormBuilderSerializer.deserialize(form, data)

        return ''


def new_form(view):
    template_name = 'admin/form_create.html'

    breadcrumbs = [
        {'text': _('Forms'), 'url': url_for('formsview.index')},
        _('Create Form')]

    web_form = FormForm()

    if not web_form.validate_on_submit():
        context = {
            'breadcrumbs': breadcrumbs,
            'form': web_form
        }

        return view.render(template_name, **context)

    form = models.Form(deployment_id=g.event.deployment_id)
    web_form.populate_obj(form)
    form.save()

    # add default role permissions for this form
    roles = models.Role.query.filter_by(
        deployment_id=g.event.deployment_id).all()
    form.roles = roles
    form.save()

    return redirect(url_for('formsview.index'))


def edit_form(view, form_id):
    template_name = 'admin/form_edit.html'

    form = models.Form.query.filter_by(id=form_id).first_or_404()
    breadcrumbs = [
        {'text': _('Forms'), 'url': url_for('formsview.index')},
        _('Edit Form')]
    web_form = FormForm(obj=form)

    if not web_form.validate_on_submit():
        context = {
            'breadcrumbs': breadcrumbs,
            'form': web_form,
        }

        return view.render(template_name, **context)

    web_form.populate_obj(form)
    form.save()

    return redirect(url_for('formsview.index'))


def forms_list(view):
    template_name = 'admin/form_list.html'

    breadcrumbs = [_('Forms')]

    forms = models.Form.query.order_by('name').all()
    checklist_init_form = make_checklist_init_form(g.event)
    form_import_form = FormImportForm()

    context = {
        'forms': forms,
        'breadcrumbs': breadcrumbs,
        'init_form': checklist_init_form,
        'form_import_form': form_import_form,
    }

    return view.render(template_name, **context)


def quality_assurance(view, form_id):
    template_name = 'admin/quality_assurance.html'
    form = models.Form.query.filter_by(id=form_id).first_or_404()

    breadcrumbs = [
        {'text': _('Forms'), 'url': url_for('formsview.index')},
        _('Quality Assurance'), form.name]
    failed_checks = []

    if request.method == 'POST':
        from apollo.submissions.qa.query_builder import generate_qa_query
        try:
            postdata = json.loads(request.form.get('postdata'))
            form.quality_checks = []
            posted_check_data = []
            for index, item in enumerate(postdata):
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
                    posted_check_data.append([
                        desc, lhs, comp, rhs
                    ])
                    expression = f'{lhs} {comp} {rhs}'
                    try:
                        # check that we have a valid expression,
                        # and if so, add it to the form's QA
                        generate_qa_query(expression, form)
                        form.quality_checks.append({
                            'name': generate_identifier(), 'description': desc,
                            'lvalue': lhs, 'comparator': comp,
                            'rvalue': rhs
                        })
                    except ValueError:
                        failed_checks.append(index)

            # display the page again if there are any errors
            if failed_checks:
                context = {
                    'page_title': page_title,
                    'check_data': posted_check_data,
                    'failed_checks': failed_checks
                }
                return render_template(template_name, **context)

            form.save()

            return redirect(url_for('formsview.index'))
        except ValueError:
            pass

    check_data = [
        (c['description'], c['lvalue'], c['comparator'], c['rvalue'])
        for c in form.quality_checks
    ] if form.quality_checks else [[''] * 4]

    context = {
        'breadcrumbs': breadcrumbs,
        'check_data': check_data,
        'failed_checks': failed_checks
    }

    return view.render(template_name, **context)


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

    return redirect(url_for('formsview.index'))
