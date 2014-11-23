# -*- coding: utf-8 -*-
from __future__ import absolute_import
from collections import OrderedDict
from functools import partial
from flask import Blueprint, render_template, request, url_for
from flask.ext.babel import lazy_gettext as _
from flask.ext.menu import register_menu
from flask.ext.security import login_required
from ..analyses.common import (
    generate_incidents_data, generate_process_data
)
from mongoengine import Q
from ..submissions.models import FLAG_STATUSES
from ..services import forms, locations, location_types, submissions
from . import route, permissions, filters
from .helpers import analysis_breadcrumb_data, analysis_navigation_data


def get_analysis_menu():
    return [{
        'url': url_for('analysis.process_analysis', form_id=unicode(form.pk)),
        'text': form.name,
    } for form in forms.find().filter(
        Q(form_type='INCIDENT') |
        Q(form_type='CHECKLIST', groups__fields__analysis_type='PROCESS')
    ).order_by('form_type')]


def get_result_analysis_menu():
    return [{
        'url': url_for(
            'analysis.results_analysis', form_id=unicode(form.pk)),
        'text': form.name
    } for form in forms.find(
        form_type='CHECKLIST',
        groups__fields__analysis_type='RESULT'
    ).order_by('form_type')]


bp = Blueprint('analysis', __name__, template_folder='templates',
               static_folder='static', static_url_path='/core/static')


def _process_analysis(form_id, location_id=None, tag=None):
    form = forms.get_or_404(pk=form_id)
    location = locations.get_or_404(pk=location_id) \
        if location_id else locations.root()

    template_name = ''
    tags = []
    page_title = _(u'%(form)s Analysis', form=form.name)
    grouped = False
    display_tag = None
    filter_class = filters.generate_submission_analysis_filter(form)

    # set the correct template and fill out the required data
    if form.form_type == 'CHECKLIST':
        if tag:
            template_name = 'frontend/checklist_summary_breakdown.html'
            tags.append(tag)
            display_tag = tag
            grouped = True
        else:
            template_name = 'frontend/checklist_summary.html'
            tags.extend([
                field.name for group in form.groups
                for field in group.fields if field.analysis_type == 'PROCESS'
            ])
            grouped = False

        queryset = submissions.find(
            form=form, submission_type='M').filter_in(location)
    else:
        grouped = True
        queryset = submissions.find(form=form).filter_in(location)
        template_name = 'frontend/critical_incident_summary.html'

        if tag:
            # a slightly different filter, one prefiltering
            # on the specified tag
            display_tag = tag
            template_name = 'frontend/critical_incidents_locations.html'
            filter_class = \
                filters.generate_critical_incident_location_filter(tag)

    # create data filter
    filter_set = filter_class(queryset, request.args)

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


def _voting_results(form_pk, location_pk=None):
    form = forms.get_or_404(
        pk=form_pk, form_type='CHECKLIST',
        groups__fields__analysis_type='RESULT')
    if location_pk is None:
        location = locations.root()
    else:
        location = locations.get_or_404(pk=location_pk)

    template_name = 'frontend/results.html'
    page_title = _(u'%(form_name)s Voting Results', form_name=form.name)
    filter_class = filters.generate_submission_analysis_filter(form)

    # define the condition for which a submission should be included
    result_fields = filter(
        lambda field: field.analysis_type == 'RESULT',
        [field for group in form.groups
         for field in group.fields])
    result_field_labels = [field.name for field in result_fields]
    result_field_descriptions = [field.description for field in result_fields]

    valid_conditions = dict(
        ('{}__exists'.format(field), True) for field in result_field_labels)

    queryset = submissions.find(
        form=form,
        submission_type='M',
        verification_status__ne=FLAG_STATUSES['rejected'][0],
        quarantine_status__nin=['A', 'R'],
        )
    filter_set = filter_class(queryset, request.args)
    dataset = filter_set.qs.to_dataframe()
    convergence_dataset = filter_set.qs.filter(
        **valid_conditions).to_dataframe()

    loc_types = [lt for lt in location_types.root().children
                 if lt.is_political is True]
    location_tree = {
        lt.name: locations.find(
            location_type=lt.name
        ).order_by('name') for lt in loc_types
    }

    chart_data = {}

    # restrict the convergence dataframe to result fields and compute the
    # cummulative sum
    if not convergence_dataset.empty:
        convergence_df = convergence_dataset.sort(
            'updated')[['updated'] + result_field_labels]
        for field in result_field_labels:
            convergence_df[field] = convergence_df[field].cumsum()

        # compute vote proportions A / (A + B + C + ...)
        convergence_df[result_field_labels] = \
            convergence_df[result_field_labels].div(
                convergence_df[result_field_labels].sum(axis=1), axis=0)

        for component in result_field_labels:
            chart_data[component] = map(
                lambda (ts, f): (int(ts.strftime('%s')) * 1000, f * 100),
                convergence_df.as_matrix(['updated', component]))

    context = {
        'page_title': page_title,
        'filter_form': filter_set.form,
        'location': location,
        'dataframe': dataset,
        'form': form,
        'result_labels': result_field_labels,
        'result_descriptions': result_field_descriptions,
        'chart_data': chart_data,
        'chart_series': result_field_labels,
        'location_types': loc_types,
        'location_tree': location_tree,
        'breadcrumb_data': analysis_breadcrumb_data(
            form, location, analysis_type='results'),
        'navigation_data': analysis_navigation_data(
            form, location, analysis_type='results')
    }

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


@route(bp, '/submissions/analysis/results/form/<form_id>')
@register_menu(bp, 'results_analysis', _('Results Analysis'),
               dynamic_list_constructor=partial(get_result_analysis_menu),
               visible_when=lambda: permissions.view_analyses.can())
@permissions.view_analyses.require(403)
@login_required
def results_analysis(form_id):
    return _voting_results(form_id)


@route(bp, '/submissions/analysis/results/form/<form_id>/location/<location_id>')
@permissions.view_analyses.require(403)
@login_required
def results_analysis_with_location(form_id, location_id):
    return _voting_results(form_id, location_id)
