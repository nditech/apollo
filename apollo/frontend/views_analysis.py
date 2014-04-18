# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from collections import OrderedDict
from flask import Blueprint, render_template, request
from flask.ext.babel import lazy_gettext as _
from flask.ext.menu import register_menu
from ..analyses.common import (
    generate_incidents_data, generate_process_data
)
from ..services import forms, locations, location_types, submissions
from .filters import (
    generate_submission_analysis_filter,
    generate_critical_incident_location_filter
)


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
    analysis_filter = generate_submission_analysis_filter(form)

    # set the correct template and fill out the required data
    if form.form_type == 'CHECKLIST':
        if tag:
            template_name = 'frontend/checklist_summary_breakdown.html'
            tags.append[tag]
            display_tag = tag
            grouped = True
        else:
            template_name = 'frontend/checklist_summary.html'
            tags.extend([
                field.name for group in form.groups
                for field in group.fields if field.analysis_type == 'PROCESS'
            ])
            grouped = False

        queryset = submissions(form=form, contributor=None).filter_in(location)
    else:
        grouped = True
        queryset = submissions(form=form).filter_in(location)
        template_name = 'frontend/critical_incident_summary.html'

        if tag:
            # a slightly different filter, one prefiltering
            # on the specified tag
            display_tag = tag
            template_name = 'frontend/critical_incident_locations.html'
            analysis_filter = generate_critical_incident_location_filter(tag)

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

    for group in form.groups:
        process_fields = sorted([
            field.name for field in group.fields
            if field.analysis_type == 'PROCESS'])
        context['field_groups'][group.name] = process_fields

    # processing for incident forms
    if form.form_type == 'INCIDENT':
        if display_tag:
            context['form_field'] = form.get_field_by_tag(display_tag)
            context['location_types'] = location_types.find(
                on_analysis_view=True)
            context['incidents'] = filter_set.qs
        else:
            context['incident_summary'] = generate_incidents_data(form, filter_set.qs, location, grouped)
    else:
        context['process_summary'] = generate_process_data(form, filter_set.qs, location, grouped=True)

    return render_template(template_name, **context)
