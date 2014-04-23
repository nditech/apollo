# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from collections import OrderedDict
from functools import partial
from flask import Blueprint, render_template, request, url_for
from flask.ext.babel import lazy_gettext as _
from flask.ext.menu import register_menu
from flask.ext.security import login_required
from ..analyses.common import (
    generate_incidents_data, generate_process_data
)
from ..services import forms, locations, location_types, submissions
from . import route, permissions, filters
from .helpers import analysis_breadcrumb_data, analysis_navigation_data


def get_analysis_menu():
    return [{
        'url': url_for('analysis.process_analysis', form_id=unicode(form.pk)),
        'text': form.name,
    } for form in forms.find().order_by('form_type')]


bp = Blueprint('analysis', __name__, template_folder='templates',
               static_folder='static', static_url_path='/core/static')


def _process_analysis(form_id, location_id=None, tag=None):
    form = forms.get_or_404(pk=form_id)
    location = locations.get_or_404(pk=location_id) \
        if location_id else locations.root()

    template_name = ''
    tags = []
    page_title = _('%(form)s Analysis', form=form.name)
    grouped = False
    display_tag = None
    analysis_filter = filters.generate_submission_analysis_filter(form)

    # set the correct template and fill out the required data
    if form.form_type == 'CHECKLIST':
        if tag:
            template_name = 'frontend/nu_checklist_summary_breakdown.html'
            tags.append(tag)
            display_tag = tag
            grouped = True
        else:
            template_name = 'frontend/nu_checklist_summary.html'
            tags.extend([
                field.name for group in form.groups
                for field in group.fields if field.analysis_type == 'PROCESS'
            ])
            grouped = False

        queryset = submissions.find(
            form=form, contributor=None).filter_in(location)
    else:
        grouped = True
        queryset = submissions.find(form=form).filter_in(location)
        template_name = 'frontend/nu_critical_incident_summary.html'

        if tag:
            # a slightly different filter, one prefiltering
            # on the specified tag
            display_tag = tag
            template_name = 'frontend/nu_critical_incident_locations.html'
            analysis_filter = \
                filters.generate_critical_incident_location_filter(tag)

    # create data filter
    filter_set = analysis_filter(queryset, request.args)

    # set up template context
    context = {}
    context['dataframe'] = filter_set.qs.to_dataframe()
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

    for group in form.groups:
        process_fields = sorted([
            field for field in group.fields
            if field.analysis_type == 'PROCESS'], key=lambda x: x.name)
        context['field_groups'][group.name] = process_fields

    # processing for incident forms
    if form.form_type == 'INCIDENT':
        if display_tag:
            context['form_field'] = form.get_field_by_tag(display_tag)
            context['location_types'] = location_types.find(
                on_analysis_view=True)
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


@route(bp, '/submissions/analysis/process/form/<form_id>')
@register_menu(bp, 'process_analysis', _('Process Analysis'),
               dynamic_list_constructor=partial(get_analysis_menu),
               visible_when=lambda: permissions.view_analyses.can())
@permissions.view_analyses.require(403)
@login_required
def process_analysis(form_id):
    return _process_analysis(form_id)


@route(bp, '/submissions/analysis/process/form/<form_id>/location/<location_id>')
@permissions.view_analyses.require(403)
@login_required
def process_analysis_with_location(form_id, location_id):
    return _process_analysis(form_id, location_id)


@route(bp, '/submissions/analysis/process/form/<form_id>/location/<location_id>/tag/<tag>')
@permissions.view_analyses.require(403)
@login_required
def process_analysis_with_location_and_tag(form_id, location_id, tag):
    return _process_analysis(form_id, location_id, tag)
