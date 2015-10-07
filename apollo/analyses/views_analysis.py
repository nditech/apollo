# -*- coding: utf-8 -*-
from __future__ import absolute_import
from collections import OrderedDict
from functools import partial
from flask import Blueprint, render_template, request, url_for, current_app
from flask.ext.babel import lazy_gettext as _
from flask.ext.menu import register_menu
from flask.ext.security import login_required
from apollo.analyses.common import (
    generate_incidents_data, generate_process_data
)
from mongoengine import Q
from apollo.submissions.models import FLAG_STATUSES
from apollo.services import forms, locations, location_types, submissions
from apollo.frontend import route, permissions, filters
from apollo.frontend.helpers import (
    analysis_breadcrumb_data,
    analysis_navigation_data
)
import math
import pandas as pd


def get_analysis_menu():
    return [{
        'url': url_for('analysis.process_analysis', form_id=unicode(form.pk)),
        'text': form.name,
        'icon': '<i class="glyphicon glyphicon-stats"></i>'
    } for form in forms.find().filter(
        Q(form_type='INCIDENT') |
        Q(form_type='CHECKLIST', groups__fields__analysis_type='PROCESS')
    ).order_by('form_type', 'name')]


def get_result_analysis_menu():
    return [{
        'url': url_for(
            'analysis.results_analysis', form_id=unicode(form.pk)),
        'text': form.name,
        'icon': '<i class="glyphicon glyphicon-stats"></i>'
    } for form in forms.find(
        form_type='CHECKLIST',
        groups__fields__analysis_type='RESULT'
    ).order_by('form_type', 'name')]


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
            form=form, submission_type='M',
            quarantine_status__nin=['A']).filter_in(location)
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

    loc_types = [lt for lt in location_types.root().children
                 if lt.is_political is True]
    location_tree = {
        lt.name: locations.find(
            location_type=lt.name
        ).order_by('name') for lt in loc_types
    }

    # define the condition for which a submission should be included
    result_fields = filter(
        lambda field: field.analysis_type == 'RESULT',
        [field for group in form.groups
         for field in group.fields])
    result_field_labels = [field.name for field in result_fields]
    result_field_descriptions = [field.description for field in result_fields]

    queryset = submissions.find(
        form=form,
        submission_type='M',
        verification_status__ne=FLAG_STATUSES['rejected'][0],
        quarantine_status__nin=['A', 'R'],
        )
    filter_set = filter_class(queryset, request.args)
    dataset = filter_set.qs.to_dataframe()

    registered_voters_field = form.registered_voters_tag or 'registered_voters'
    if form.invalid_votes_tag:
        rejected_votes_field = [form.invalid_votes_tag]
    else:
        rejected_votes_field = []
    if form.blank_votes_tag:
        blank_votes_field = [form.blank_votes_tag]
    else:
        blank_votes_field = []

    # compute and store reporting status
    dataset['reported'] = dataset[
        result_field_labels + [registered_voters_field]].count(1) == len(
        result_field_labels) + 1
    dataset['missing'] = dataset[
        result_field_labels + [registered_voters_field]].count(1) != len(
        result_field_labels) + 1

    try:
        overall_summation = dataset.groupby(
            location.location_type).sum().ix[location.name]
        valid_dataframe = dataset[dataset.reported==True].query(
            u'%s==u"%s"' % (location.location_type, location.name))
        valid_summation = dataset[dataset.reported==True].fillna(0).groupby(
            location.location_type).sum().ix[location.name]
        reporting = overall_summation[['missing', 'reported']]
        reporting['reported_pct'] = reporting['reported']/(
            reporting['reported'] + reporting['missing'])
        reporting['missing_pct'] = reporting['missing']/(
            reporting['reported'] + reporting['missing'])

        data_analyses = {'overall': {}, 'grouped': {}}
        data_analyses['overall'] = {
            'reported_cnt': int(reporting['reported']),
            'missing_cnt': int(reporting['missing']),
            'reported_pct': reporting['reported_pct'],
            'missing_pct': reporting['missing_pct'],
            'rv': valid_summation.get(registered_voters_field, 0),
            'all_votes': int(
                valid_summation[
                    result_field_labels + rejected_votes_field +
                    blank_votes_field].sum(
                    axis=1)),
            'turnout': valid_summation[
                result_field_labels + rejected_votes_field +
                blank_votes_field].sum(axis=1) /
            valid_summation.get(registered_voters_field, 0) or pd.np.inf,
            'all_valid_votes': int(
                valid_summation[result_field_labels].sum(axis=1)),
            'all_valid_votes_pct': valid_summation[result_field_labels].sum(
                axis=1) / valid_summation[result_field_labels +
                                          rejected_votes_field +
                                          blank_votes_field].sum(axis=1),
            'total_rejected': int(valid_summation[rejected_votes_field[0]])
            if rejected_votes_field else 0,
            'total_rejected_pct': valid_summation[rejected_votes_field[0]] /
            valid_summation[
                result_field_labels + rejected_votes_field +
                blank_votes_field].sum(
                axis=1) if rejected_votes_field else 0,
            'total_blanks': int(valid_summation[blank_votes_field[0]])
            if blank_votes_field else 0,
            'total_blanks_pct': valid_summation[blank_votes_field[0]] /
            valid_summation[
                result_field_labels + rejected_votes_field +
                blank_votes_field].sum(
                axis=1) if blank_votes_field else 0
        }
        if form.calculate_moe and current_app.config.get('ENABLE_MOE'):
            data_analyses['overall']['turnout_moe_95'] = \
                _margin_of_error(
                    valid_dataframe, result_field_labels +
                    rejected_votes_field + blank_votes_field,
                    [registered_voters_field])
            data_analyses['overall']['turnout_moe_99'] = \
                _margin_of_error(
                    valid_dataframe, result_field_labels +
                    rejected_votes_field + blank_votes_field,
                    [registered_voters_field], 2.58)
            data_analyses['overall']['all_valid_votes_moe_95'] = \
                _margin_of_error(
                    valid_dataframe, result_field_labels,
                    result_field_labels + rejected_votes_field +
                    blank_votes_field)
            data_analyses['overall']['all_valid_votes_moe_99'] = \
                _margin_of_error(
                    valid_dataframe, result_field_labels,
                    result_field_labels + rejected_votes_field +
                    blank_votes_field, 2.58)
            data_analyses['overall']['total_rejected_moe_95'] = \
                _margin_of_error(
                    valid_dataframe, rejected_votes_field[0],
                    result_field_labels + rejected_votes_field +
                    blank_votes_field) if rejected_votes_field else 0
            data_analyses['overall']['total_rejected_moe_99'] = \
                _margin_of_error(
                    valid_dataframe, rejected_votes_field[0],
                    result_field_labels + rejected_votes_field +
                    blank_votes_field, 2.58) if rejected_votes_field else 0
            data_analyses['overall']['total_blanks_moe_95'] = \
                _margin_of_error(
                    valid_dataframe, blank_votes_field[0],
                    result_field_labels + rejected_votes_field +
                    blank_votes_field) if blank_votes_field else 0
            data_analyses['overall']['total_blanks_moe_99'] = \
                _margin_of_error(
                    valid_dataframe, blank_votes_field[0],
                    result_field_labels + rejected_votes_field +
                    blank_votes_field, 2.58) if blank_votes_field else 0
        data_available = True
    except KeyError:
        data_analyses = {'overall': {}, 'grouped': {}}
        data_analyses['overall'] = {
            'reported_cnt': 0, 'missing_cnt': 0,
            'reported_pct': 0, 'missing_pct': 0,
            'rv': 0, 'all_votes': 0, 'turnout': 0,
            'all_valid_votes': 0, 'all_valid_votes_pct': 0,
            'total_rejected': 0, 'total_rejected_pct': 0,
            'turnout_moe_95': 0, 'turnout_moe_99': 0,
            'all_valid_votes_moe_95': 0, 'all_valid_votes_moe_99': 0,
            'total_rejected_moe_95': 0, 'total_rejected_moe_99': 0,
            'total_blanks_moe_95': 0, 'total_blanks_moe_99': 0
        }
        data_available = False

    for result_field_label in result_field_labels:
        data_analyses['overall'][u'{}_cnt'.format(result_field_label)] = \
            valid_summation.get(result_field_label, 0) if data_available else 0
        data_analyses['overall'][u'{}_pct'.format(result_field_label)] = \
            valid_summation.get(result_field_label, 0) / float(
                data_analyses['overall']['all_valid_votes']) \
            if data_available else 0  # all_votes?
        if form.calculate_moe and current_app.config.get('ENABLE_MOE'):
            data_analyses['overall'][u'{}_moe_95'.format(
                result_field_label)] = _margin_of_error(
                valid_dataframe, result_field_label,
                result_field_labels) \
                if data_available else 0
            data_analyses['overall'][u'{}_moe_99'.format(
                result_field_label)] = _margin_of_error(
                valid_dataframe, result_field_label,
                result_field_labels, 2.58) \
                if data_available else 0

    # grouped summaries
    for location_type in location_tree.keys():
        data_analyses['grouped'][location_type] = []

        try:
            grouped_summation = dataset.groupby(
                location_type).sum()
            grouped_valid_summation = dataset[dataset.reported==True].groupby(
                location_type).sum()

            for sublocation in location_tree[location_type]:
                try:
                    _overall = grouped_summation.ix[sublocation.name]
                    _valid = grouped_valid_summation.fillna(
                        0).ix[sublocation.name]
                    _valid_dataframe = dataset[dataset.reported==True].query(
                        u'%s==u"%s"' % (location_type, sublocation.name))

                    _reporting = _overall[['missing', 'reported']]
                    _reporting['reported_pct'] = _reporting['reported'] / (
                        _reporting['reported'] + _reporting['missing'])
                    _reporting['missing_pct'] = _reporting['missing'] / (
                        _reporting['reported'] + _reporting['missing'])

                    _sublocation_report = {
                        'name': sublocation.name,
                        'location_type': sublocation.location_type,
                        'reported_cnt': int(_reporting['reported']),
                        'reported_pct': _reporting['reported_pct'],
                        'missing_cnt': int(_reporting['missing']),
                        'missing_pct': _reporting['missing_pct'],
                        'rv': _valid.get(registered_voters_field, 0),
                        'all_votes': int(
                            _valid[result_field_labels +
                                   rejected_votes_field +
                                   blank_votes_field].sum(
                                axis=1)),
                        'turnout': _valid[
                            result_field_labels + rejected_votes_field +
                            blank_votes_field].sum(
                            axis=1) / _valid.get(
                            registered_voters_field, 0) or pd.np.inf,
                        'all_valid_votes': int(
                            _valid[result_field_labels].sum(axis=1)),
                        'all_valid_votes_pct': _valid[result_field_labels].sum(
                            axis=1) / _valid[result_field_labels +
                                             rejected_votes_field +
                                             blank_votes_field].sum(axis=1),
                        'total_rejected': int(_valid[rejected_votes_field[0]])
                        if rejected_votes_field else 0,
                        'total_rejected_pct': _valid[rejected_votes_field[0]] /
                        _valid[result_field_labels + rejected_votes_field +
                               blank_votes_field].sum(
                            axis=1) if rejected_votes_field else 0,
                        'total_blanks': int(_valid[blank_votes_field[0]])
                        if blank_votes_field else 0,
                        'total_blanks_pct': _valid[blank_votes_field[0]] /
                        _valid[result_field_labels + rejected_votes_field +
                               blank_votes_field].sum(
                            axis=1) if blank_votes_field else 0,
                    }

                    if (
                        form.calculate_moe and current_app.config.get(
                            'ENABLE_MOE')
                    ):
                        _sublocation_report['turnout_moe_95'] = \
                            _margin_of_error(
                                _valid_dataframe, result_field_labels +
                                rejected_votes_field + blank_votes_field,
                                [registered_voters_field])
                        _sublocation_report['turnout_moe_99'] = \
                            _margin_of_error(
                                _valid_dataframe, result_field_labels +
                                rejected_votes_field + blank_votes_field,
                                [registered_voters_field],
                                2.58)
                        _sublocation_report['all_valid_votes_moe_95'] = \
                            _margin_of_error(
                                _valid_dataframe, result_field_labels,
                                result_field_labels + rejected_votes_field +
                                blank_votes_field)
                        _sublocation_report['all_valid_votes_moe_99'] = \
                            _margin_of_error(
                                _valid_dataframe, result_field_labels,
                                result_field_labels + rejected_votes_field +
                                blank_votes_field,
                                2.58)
                        _sublocation_report['total_rejected_moe_95'] = \
                            _margin_of_error(
                                _valid_dataframe, rejected_votes_field[0],
                                result_field_labels + rejected_votes_field +
                                blank_votes_field) \
                            if rejected_votes_field else 0
                        _sublocation_report['total_rejected_moe_99'] = \
                            _margin_of_error(
                                _valid_dataframe, rejected_votes_field[0],
                                result_field_labels + rejected_votes_field +
                                blank_votes_field,
                                2.58) \
                            if rejected_votes_field else 0
                        _sublocation_report['total_blanks_moe_95'] = \
                            _margin_of_error(
                                _valid_dataframe, blank_votes_field[0],
                                result_field_labels + rejected_votes_field +
                                blank_votes_field) \
                            if blank_votes_field else 0
                        _sublocation_report['total_blanks_moe_99'] = \
                            _margin_of_error(
                                _valid_dataframe, blank_votes_field[0],
                                result_field_labels + rejected_votes_field +
                                blank_votes_field,
                                2.58) \
                            if blank_votes_field else 0
                    data_available = True
                except KeyError:
                    data_available = False
                    _sublocation_report = {
                        'name': sublocation.name,
                        'location_type': sublocation.location_type,
                        'reported_cnt': 0,
                        'reported_pct': 0,
                        'missing_cnt': 0,
                        'missing_pct': 0,
                        'rv': 0,
                        'all_votes': 0,
                        'turnout': 0,
                        'all_valid_votes': 0,
                        'all_valid_votes_pct': 0,
                        'total_rejected': 0,
                        'total_rejected_pct': 0,
                        'turnout_moe_95': 0,
                        'turnout_moe_99': 0,
                        'all_valid_votes_moe_95': 0,
                        'all_valid_votes_moe_99': 0,
                        'total_rejected_moe_95': 0,
                        'total_rejected_moe_99': 0,
                        'total_blanks_moe_95': 0,
                        'total_blanks_moe_99': 0
                    }

                for result_field_label in result_field_labels:
                    _sublocation_report[u'{}_cnt'.format(
                        result_field_label)] = _valid.get(
                        result_field_label, 0) if data_available else 0
                    _sublocation_report[u'{}_pct'.format(
                        result_field_label)] = _valid.get(
                        result_field_label, 0) / float(
                        _sublocation_report['all_valid_votes']) \
                        if data_available else 0

                    if (
                        form.calculate_moe and current_app.config.get(
                            'ENABLE_MOE')
                    ):
                        _sublocation_report[u'{}_moe_95'.format(
                            result_field_label)] = _margin_of_error(
                            _valid_dataframe, result_field_label,
                            result_field_labels) \
                            if data_available else 0
                        _sublocation_report[u'{}_moe_99'.format(
                            result_field_label)] = _margin_of_error(
                            _valid_dataframe, result_field_label,
                            result_field_labels,
                            2.58) if data_available else 0
                data_analyses['grouped'][location_type].append(
                    _sublocation_report)
        except IndexError:
            pass

    convergence_dataset = dataset[dataset.reported==True]

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
        'result_fields': result_fields,
        'data_analyses': data_analyses,
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
@register_menu(
    bp, 'main.analyses',
    _('Analyses'), order=4,
    icon='<i class="glyphicon glyphicon-stats"></i>',
    visible_when=lambda: len(get_analysis_menu()) > 0
    and permissions.view_analyses.can())
@register_menu(
    bp, 'main.analyses.process_analysis',
    _('Process Analysis'),
    icon='<i class="glyphicon glyphicon-stats"></i>',
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
@register_menu(
    bp, 'main.analyses',
    _('Analyses'), order=4,
    visible_when=lambda: len(get_result_analysis_menu()) > 0
    and permissions.view_analyses.can())
@register_menu(
    bp, 'main.analyses.results_analysis',
    _('Results Analysis'),
    icon='<i class="glyphicon glyphicon-stats"></i>',
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


def _point_estimate(dataframe, numerator, denominator):
    if not isinstance(numerator, list):
        numerator = [numerator]
    m = dataframe.ix[:, denominator].sum(axis=1)
    mbar = m.sum(axis=0) / m.size
    return dataframe.ix[:, numerator].sum(axis=0).sum(axis=0) / (mbar * m.size)


def _variance(dataframe, numerator, denominator):
    p = _point_estimate(dataframe, numerator, denominator)
    psquared = p * p

    m = dataframe.ix[:, denominator].sum(axis=1)
    msquared = m * m

    if isinstance(numerator, list):
        a = dataframe.ix[:, numerator].sum(axis=1)
    else:
        a = dataframe.ix[:, [numerator]].sum(axis=1)
    asquared = a * a

    mbar = m.sum(axis=0) / m.size
    mbarsquared = mbar * mbar

    f = m.sum(axis=0) / current_app.config.get('BIG_N')
    k = m.size
    am = a * m
    sigma_asquared = asquared.sum(axis=0)
    sigma_msquared = msquared.sum(axis=0)
    sigma_am = am.sum(axis=0)

    return (
        (1 - f) / (k * mbarsquared)) * ((sigma_asquared -
                                    (2 * p * sigma_am) +
                                    (psquared * sigma_msquared)) / (k - 1))


def _margin_of_error(dataframe, numerator, denominator, cv=1.96):
    moe = round(math.sqrt(abs(_variance(
        dataframe, numerator, denominator))) * cv * 100, 2)
    if pd.np.isnan(moe) or pd.np.isinf(moe):
        moe = 0
    return moe
