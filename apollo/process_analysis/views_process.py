# -*- coding: utf-8 -*-
from collections import OrderedDict
from functools import partial
from operator import itemgetter

from flask import Blueprint, g, render_template, request, url_for
from flask_babelex import lazy_gettext as _
from flask_menu import register_menu
from flask_security import login_required
from apollo.process_analysis.common import (
    generate_incidents_data, generate_process_data
)
from sqlalchemy import and_, or_

from apollo import models
from apollo.services import forms, locations, location_types, submissions
from apollo.frontend import route, permissions
from apollo.frontend.helpers import (
    analysis_breadcrumb_data,
    analysis_navigation_data
)
from apollo.submissions import filters
from apollo.submissions.utils import make_submission_dataframe


def get_analysis_menu():
    return [{
        'url': url_for('process_analysis.process_analysis',
                       form_id=form.id),
        'text': form.name,
        'icon': '<i class="glyphicon glyphicon-stats"></i>'
    } for form in forms.filter(
        or_(
            models.Form.form_type == 'INCIDENT',
            and_(
                models.Form.form_type == 'CHECKLIST',
                models.Form.data['groups'].op('@>')(
                    [{'fields': [{'analysis_type': 'PROCESS'}]}]))
        )
    ).order_by(models.Form.form_type, models.Form.name)]


def get_process_analysis_menu():
    return [{
        'url': url_for('process_analysis.process_analysis',
                       form_id=form.id),
        'text': form.name,
        'icon': '<i class="glyphicon glyphicon-stats"></i>'
    } for form in forms.filter(
        or_(
            models.Form.form_type == 'INCIDENT',
            and_(
                models.Form.form_type == 'CHECKLIST',
                models.Form.data['groups'].op('@>')(
                    [{'fields': [{'analysis_type': 'PROCESS'}]}])))
    ).order_by(models.Form.form_type, models.Form.name)]


bp = Blueprint('process_analysis', __name__, template_folder='templates',
               static_folder='static', static_url_path='/core/static')


def _process_analysis(event, form_id, location_id=None, tag=None):
    form = forms.fget_or_404(id=form_id)
    location = locations.fget_or_404(id=location_id) \
        if location_id else locations.root(event.location_set_id)

    template_name = ''
    tags = []
    page_title = _('%(form)s Analysis', form=form.name)
    grouped = False
    display_tag = None
    event = g.event
    filter_class = filters.make_submission_analysis_filter(event, form)

    location_ids = models.LocationPath.query.with_entities(
        models.LocationPath.descendant_id).filter_by(
            ancestor_id=location.id, location_set_id=event.location_set_id)

    # set the correct template and fill out the required data
    if form.form_type == 'CHECKLIST':
        if tag:
            template_name = 'process_analysis/checklist_summary_breakdown.html'
            tags.append(tag)
            display_tag = tag
            grouped = True
        else:
            template_name = 'process_analysis/checklist_summary.html'
            form._populate_field_cache()
            tags.extend([
                f['tag'] for f in form._field_cache.values()
                if f['analysis_type'] == 'PROCESS'
            ])
            grouped = False

        queryset = submissions.find(
            event=event,
            form=form, submission_type='M',
            quarantine_status='A').filter(
                models.Submission.location_id.in_(location_ids))
    else:
        grouped = True
        queryset = submissions.find(form=form).filter(
            models.Submission.location_id.in_(location_ids))
        template_name = 'process_analysis/critical_incident_summary.html'

        if tag:
            # a slightly different filter, one prefiltering
            # on the specified tag
            display_tag = tag
            template_name = 'process_analysis/critical_incidents_locations.html'
            filter_class = \
                filters.make_incident_location_filter(event, form, tag)

    # create data filter
    filter_set = filter_class(queryset, request.args)

    # set up template context
    context = {}
    context['dataframe'] = make_submission_dataframe(filter_set.qs)
    context['page_title'] = page_title
    context['display_tag'] = display_tag
    context['filter_form'] = filter_set.form
    context['form'] = form
    context['location'] = location
    context['field_groups'] = OrderedDict()
    context['breadcrumb_data'] = analysis_breadcrumb_data(
        form, location, display_tag)
    context['navigation_data'] = analysis_navigation_data(
        form, location, display_tag)

    for group in form.data['groups']:
        process_fields = sorted([
            field for field in group['fields']
            if field['analysis_type'] == 'PROCESS'], key=itemgetter('tag'))
        context['field_groups'][group['name']] = process_fields

    # processing for incident forms
    if form.form_type == 'INCIDENT':
        if display_tag:
            context['form_field'] = form.get_field_by_tag(display_tag)
            context['location_types'] = location_types.find(
                is_political=True)
            context['incidents'] = filter_set.qs
        else:
            incidents_summary = generate_incidents_data(
                form, filter_set.qs, location, grouped, tags)
            context['incidents_summary'] = incidents_summary
    else:
        process_summary = generate_process_data(
            form, filter_set.qs, location, grouped=True, tags=tags)
        context['process_summary'] = process_summary

    return render_template(template_name, **context)


@route(bp, '/submissions/analysis/process/form/<int:form_id>')
@register_menu(
    bp, 'main.analyses',
    _('Analyses'), order=4,
    icon='<i class="glyphicon glyphicon-stats"></i>',
    visible_when=lambda: len(get_analysis_menu()) > 0
    and permissions.view_process_analysis.can())
@register_menu(
    bp, 'main.analyses.process_analysis',
    _('Process Analysis'),
    icon='<i class="glyphicon glyphicon-stats"></i>',
    dynamic_list_constructor=partial(get_process_analysis_menu),
    visible_when=lambda: len(get_process_analysis_menu()) > 0
    and permissions.view_process_analysis.can())
@permissions.view_process_analysis.require(403)
@login_required
def process_analysis(form_id):
    event = g.event
    return _process_analysis(event, form_id)


@route(bp, '/submissions/analysis/process/form/<int:form_id>/location/<int:location_id>')
@permissions.view_process_analysis.require(403)
@login_required
def process_analysis_with_location(form_id, location_id):
    event = g.event
    return _process_analysis(event, form_id, location_id)


@route(bp, '/submissions/analysis/process/form/<int:form_id>/location/<int:location_id>/tag/<tag>')
@permissions.view_process_analysis.require(403)
@login_required
def process_analysis_with_location_and_tag(form_id, location_id, tag):
    event = g.event
    return _process_analysis(event, form_id, location_id, tag)
