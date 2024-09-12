# -*- coding: utf-8 -*-
import json
from datetime import datetime
from io import BytesIO

from flask import (
    abort, Blueprint, flash, g, jsonify, redirect, request, send_file, session,
    url_for)
from flask_babel import gettext as _
from flask_security import current_user
from slugify import slugify

from apollo import core, models
from apollo.core import db, uploads
from apollo.formsframework.forms import (
    FormForm, FormImportForm, make_questionnaire_hidden_toggle_form)
from apollo.formsframework.models import FormBuilderSerializer
from apollo.formsframework import utils
from apollo.formsframework.api import views as api_views
from apollo.frontend.forms import (
    make_checklist_init_form, make_survey_init_form)
from apollo.submissions.tasks import init_submissions, init_survey_submissions
from apollo.users.models import UserUpload
from apollo.utils import generate_identifier, strip_bom_header

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
        questionnaire = models.Form.query.filter_by(
            id=form.data.get('form')).one()

        if len(questionnaire.tags) == 0:
            flash_category = 'danger'
            flash_message = _(
                'Checklists were not created, as the selected Form '
                'has no question codes')
        else:
            flash_category = 'info'
            flash_message = _(
                'Checklists are being created for the Event, Form, '
                'Role and Location Type you selected')

            channel = session.get('_id')
            task_kwargs = {
                'event_id': form.data['event'],
                'form_id': form.data['form'],
                'role_id': form.data['role'],
                'location_type_id': form.data['location_type'],
                'channel': channel
            }

            init_submissions.apply_async(kwargs=task_kwargs)
    else:
        flash_category = 'danger'
        flash_message = _('Checklists were not created')

    flash(str(flash_message), flash_category)
    return redirect(url_for('formsview.index'))


def survey_init():
    flash_message = ''
    flash_category = ''
    form = make_survey_init_form(g.event)

    if form.validate_on_submit():
        questionnaire = models.Form.query.filter_by(
            id=form.data.get('form')).one()

        if len(questionnaire.tags) == 0:
            flash_category = 'danger'
            flash_message = _(
                'Surveys were not created as the selected Form '
                'has no question codes')
        else:
            flash_category = 'info'
            flash_message = _(
                'Surveys are being created for the Event, Form '
                'and Participants you selected')

            user = current_user._get_current_object()
            upload_file = strip_bom_header(request.files['import_file'])
            filename = uploads.save(upload_file)
            upload = UserUpload(
                deployment_id=g.deployment.id, upload_filename=filename,
                user_id=user.id)
            upload.save()

            task_kwargs = {
                'event_id': form.data['event'],
                'form_id': form.data['form'],
                'upload_id': upload.id
            }

            init_survey_submissions.apply_async(kwargs=task_kwargs)
    else:
        flash_category = 'danger'
        flash_message = _('Surveys were not created')

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
    web_form.vote_shares.choices = []
    web_form.turnout_fields.choices = []
    web_form.result_images.choices = []

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
    field_options = [('', '')] + \
        [(tag, tag) for tag in form.tags]
    web_form = FormForm(obj=form)
    web_form.accredited_voters_tag.choices = field_options
    web_form.blank_votes_tag.choices = field_options
    web_form.invalid_votes_tag.choices = field_options
    web_form.registered_voters_tag.choices = field_options
    web_form.turnout_registered_voters_tag.choices = field_options
    web_form.vote_shares.choices = [] + \
        [(tag, tag) for tag in form.tags]
    web_form.turnout_fields.choices = [] + \
        [(tag, tag) for tag in form.tags]
    web_form.result_images.choices = [] + \
        [
            (tag, tag)
            for tag in form.tags
            if form.get_field_by_tag(tag).get('type') == 'image'
        ]

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
    show_hidden_param = 'show_all'
    template_name = 'admin/form_list.html'

    breadcrumbs = [_('Forms')]

    checklist_init_form = make_checklist_init_form(g.event)
    form_import_form = FormImportForm()
    show_hide_form = make_questionnaire_hidden_toggle_form(g.deployment)
    query_params = request.args.to_dict(flat=False)
    query = models.Form.query.order_by('name')
    show_hidden = bool(query_params.get(show_hidden_param))

    if show_hidden:
        show_toggle_link_label = _('Hide Archived')
        add_show_url_param = False
    else:
        show_toggle_link_label = _('Show All')
        add_show_url_param = True
        query = query.filter(
            models.Form.is_hidden == False).order_by('name') # noqa

    if show_hide_form.validate_on_submit():
        posted_data = show_hide_form.data.copy()
        hide_forms = True if posted_data.get('mode') == 'hide' else False
        posted_form_ids = [f.id for f in posted_data.get('forms')]
        models.Form.query.filter(models.Form.id.in_(posted_form_ids)).update(
            {'is_hidden': hide_forms})
        db.session.commit()
        db.session.expire_all()

    all_forms = query.all()
    checklist_forms = query.filter(models.Form.form_type == 'CHECKLIST').all()
    survey_forms = query.filter(models.Form.form_type == 'SURVEY').all()

    context = {
        'forms': all_forms,
        'checklist_forms': checklist_forms,
        'survey_forms': survey_forms,
        'events': models.Event.query.filter(
            models.Event.is_hidden == False
        ).order_by('name').all(),
        'roles': models.ParticipantRole.query.order_by('name').all(),
        'location_types': models.LocationType.query.all(),
        'breadcrumbs': breadcrumbs,
        'init_form': checklist_init_form,
        'form_import_form': form_import_form,
        'show_hide_form': show_hide_form,
        'show_toggle_link_label': show_toggle_link_label,
        'add_show_url_param': add_show_url_param,
        'show_hidden_param': show_hidden_param,
    }

    return view.render(template_name, **context)


def quality_controls(view, form_id):
    template_name = 'admin/quality_assurance.html'
    form = models.Form.query.filter_by(id=form_id).first_or_404()
    breadcrumbs = [
        {'text': _('Forms'), 'url': url_for('formsview.index')},
        _('Quality Assurance'), form.name]

    quality_controls = []

    if form.quality_checks:
        for quality_check in form.quality_checks:
            quality_control = {}

            quality_control['name'] = quality_check['name']
            quality_control['description'] = quality_check['description']
            quality_control['criteria'] = []

            if 'criteria' in quality_check:
                for index, criterion in enumerate(quality_check['criteria']):
                    quality_control['criteria'].append({
                        'lvalue': criterion['lvalue'],
                        'comparator': criterion['comparator'],
                        'rvalue': criterion['rvalue'],
                        'conjunction': criterion['conjunction'],
                        'id': str(index)
                    })
            else:
                quality_control['criteria'].append({
                    'lvalue': quality_check['lvalue'],
                    'comparator': quality_check['comparator'],
                    'rvalue': quality_check['rvalue'],
                    'conjunction': '&&',
                    'id': '0'
                })

            quality_controls.append(quality_control)

    context = {
        'breadcrumbs': breadcrumbs,
        'form': form,
        'quality_controls': quality_controls
    }

    return view.render(template_name, **context)

def sort_quality_controls(view, form_id):
    form = models.Form.query.filter_by(id=form_id).first_or_404()

    if request.method == 'POST':
        try:
            ordering = request.json.get('ordering')
            if form.quality_checks and ordering:
                qc_hashmap = {}
                qc_list = []
                for qc in form.quality_checks:
                    qc_hashmap[qc['name']] = qc

                for name in ordering:
                    if name in qc_hashmap:
                        qc_list.append(qc_hashmap.pop(name))
                if len(qc_hashmap.keys()) > 0:
                    for name in qc_hashmap.keys():
                        qc_list.append(qc_hashmap.pop(name))

                form.quality_checks = qc_list
                form.save()

                return jsonify({})
        except ValueError:
            abort(400, 'Bad Data')
    else:
        abort(403, 'Forbidden')

def quality_control_edit(view, form_id, qc=None):
    template_name = 'admin/quality_assurance_edit.html'
    form = models.Form.query.filter_by(id=form_id).first_or_404()
    breadcrumbs = [
        {'text': _('Forms'), 'url': url_for('formsview.index')},
        {
            'text': _('Quality Assurance'),
            'url': url_for('formsview.qc', form_id=form.id)
        },
        form.name
    ]

    if request.method == 'POST':
        try:
            postdata = json.loads(request.form.get('postdata'))
            quality_control = {}

            if 'name' in postdata and postdata['name']:
                # we have a quality control that should exist
                quality_control = next(
                    filter(
                        lambda c: c['name'] == postdata['name'],
                        form.quality_checks))

            if not quality_control:
                quality_control['name'] = generate_identifier()

            quality_control['description'] = postdata['description']
            quality_control['criteria'] = []

            for condition in postdata['criteria']:
                quality_control['criteria'].append({
                    'lvalue': condition['lvalue'],
                    'comparator': condition['comparator'],
                    'rvalue': condition['rvalue'],
                    'conjunction': condition['conjunction']
                })

            if 'rvalue' in quality_control:
                del quality_control['rvalue']
            if 'lvalue' in quality_control:
                del quality_control['lvalue']
            if 'comparator' in quality_control:
                del quality_control['comparator']

            if form.quality_checks:
                for i, control in enumerate(form.quality_checks):
                    if control['name'] == quality_control['name']:
                        form.quality_checks[i] = quality_control
                        break
                else:
                    form.quality_checks.append(quality_control)
            else:
                form.quality_checks = [quality_control]

            form.save()

            if request.is_xhr:
                data = {}
                return jsonify(data)
            else:
                return redirect(url_for('formsview.qc', form_id=form.id))
        except ValueError:
            pass

    if qc:
        try:
            quality_check = next(
                filter(lambda c: c['name'] == qc, form.quality_checks))
        except StopIteration:
            abort(404)

        criteria = []

        if 'criteria' in quality_check:
            for index, criterion in enumerate(quality_check['criteria']):
                criteria.append({
                    'lvalue': criterion['lvalue'],
                    'comparator': criterion['comparator'],
                    'rvalue': criterion['rvalue'],
                    'conjunction': criterion['conjunction'],
                    'id': str(index)
                })
        else:
            criteria.append({
                'lvalue': quality_check['lvalue'],
                'comparator': quality_check['comparator'],
                'rvalue': quality_check['rvalue'],
                'conjunction': '&&',
                'id': '0'
            })

        title = _('Edit Quality Assurance')
        is_new = 0
        quality_control = {
            'name': quality_check['name'],
            'description': quality_check['description'],
            'criteria': criteria
        }
    else:
        title = _('Add Quality Assurance')
        is_new = 1
        quality_control = {
            'name': '', 'description': '', 'criteria': [{
                'lvalue': '', 'comparator': '=', 'rvalue': '',
                'conjunction': '&&', 'id': '0'
            }]
        }

    context = {
        'title': title,
        'is_new': is_new,
        'breadcrumbs': breadcrumbs,
        'form': form,
        'participant_set': g.event.participant_set,
        'location_set': g.event.location_set,
        'quality_control': quality_control
    }

    return view.render(template_name, **context)


def quality_control_delete(view, form_id, qc):
    form = models.Form.query.filter_by(id=form_id).first_or_404()

    if request.method == 'DELETE' and request.is_xhr:
        if form.quality_checks:
            for i, control in enumerate(form.quality_checks):
                if control['name'] == qc:
                    del form.quality_checks[i]
                    break

            form.save()
            return 'true'

    return 'false'


def export_form(id):
    form = models.Form.query.filter_by(id=id).first_or_404()
    memory_file = BytesIO()
    workbook = utils.export_form(form)
    workbook.save(memory_file)
    memory_file.seek(0)
    current_timestamp = datetime.utcnow()
    filename = slugify(
        f'{form.name}-{current_timestamp:%Y %m %d %H%M%S}') + '.xls'

    return send_file(
        memory_file, attachment_filename=filename,
        as_attachment=True, mimetype='application/vnd.ms-excel')


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
