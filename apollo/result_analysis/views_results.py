# -*- coding: utf-8 -*-
from functools import partial
import math
from operator import attrgetter

from flask import (
    Blueprint, abort, current_app, g, render_template, request, url_for)
from flask_babelex import lazy_gettext as _
from flask_menu import register_menu
from flask_security import login_required
import pandas as pd
from sqlalchemy import not_

from apollo import models
from apollo.formsframework.models import Form
from apollo.frontend import route, permissions
from apollo.frontend.helpers import analysis_breadcrumb_data
from apollo.services import forms, locations, location_types, submissions
from apollo.submissions.filters import make_submission_analysis_filter
from apollo.submissions.models import FLAG_STATUSES
from apollo.submissions.utils import make_submission_dataframe


def get_result_analysis_menu():
    event = g.event
    return [{
        'url': url_for(
            'result_analysis.results_analysis', form_id=form.id),
        'text': form.name,
    } for form in forms.query.filter(
        Form.events.contains(event),
        Form.form_type == 'CHECKLIST',
        Form.vote_shares != None,   # noqa
        Form.vote_shares != []
    ).order_by('name')]


bp = Blueprint('result_analysis', __name__, template_folder='templates',
               static_folder='static', static_url_path='/core/static')


def _voting_results(form_id, location_id=None):
    event = g.event
    form = forms.filter(
        Form.vote_shares != None,   # noqa
        Form.vote_shares != [],
        Form.id == form_id,
        Form.form_type == 'CHECKLIST',
        Form.events.contains(event)
    ).first()

    if form is None:
        abort(404)

    if location_id is None:
        location = locations.root(event.location_set_id)
    else:
        location = locations.fget_or_404(pk=location_id)

    template_name = 'result_analysis/results.html'
    breadcrumbs = [_('Results Data'), form.name]
    filter_on_locations = not form.untrack_data_conflicts
    filter_class = make_submission_analysis_filter(
        event, form, filter_on_locations)

    loc_types = [lt for lt in location_types.root(
                    event.location_set_id).descendants()
                 if lt.is_political is True]

    location_tree = {}
    for lt in loc_types:
        lt_locs = models.Location.query.filter_by(location_type_id=lt.id)
        location_tree[lt.name] = sorted(lt_locs, key=attrgetter('name'))

    # define the condition for which a submission should be included
    result_fields = [
        form.get_field_by_tag(tag) for tag in form.vote_shares
    ] if form.vote_shares else []
    result_field_labels = form.vote_shares or []
    result_field_descriptions = [
        field['description'] for field in result_fields]

    query_kwargs = {'event': event, 'form': form}
    if not form.untrack_data_conflicts:
        query_kwargs['submission_type'] = 'M'
    else:
        query_kwargs['submission_type'] = 'O'

    queryset = submissions.find(**query_kwargs).filter(
        models.Submission.verification_status != FLAG_STATUSES['rejected'][0],
        not_(models.Submission.quarantine_status.in_(['A', 'R'])))
    filter_set = filter_class(queryset, request.args)
    dataset = make_submission_dataframe(filter_set.qs, form)

    registered_voters_field = form.registered_voters_tag or 'registered_voters'
    if form.invalid_votes_tag:
        rejected_votes_field = [form.invalid_votes_tag]
    else:
        rejected_votes_field = []
    if form.blank_votes_tag:
        blank_votes_field = [form.blank_votes_tag]
    else:
        blank_votes_field = []
    if form.accredited_voters_tag:
        accredited_voters_field = [form.accredited_voters_tag]
    else:
        accredited_voters_field = []

    non_null_fields = (
        rejected_votes_field
        + blank_votes_field
        + accredited_voters_field
        + result_field_labels)
    non_zero_fields = [registered_voters_field]
    non_zero_sum_fields = result_field_labels

    if not dataset.empty:
        # compute and store reporting status
        dataset['reported'] = dataset[non_null_fields].where(
            lambda x: x != pd.np.nan).join(
                dataset[non_zero_fields].where(lambda x: x > 0)
            ).assign(shares = (dataset[non_zero_sum_fields].sum(1) > 0).replace(
                False, pd.np.nan)).count(1) == len(non_null_fields) + len(non_zero_fields) + 1  # noqa
        dataset['missing'] = dataset[non_null_fields].where(
            lambda x: x != pd.np.nan).join(
                dataset[non_zero_fields].where(lambda x: x > 0)
            ).assign(shares = (dataset[non_zero_sum_fields].sum(1) > 0).replace(
                False, pd.np.nan)).count(1) != len(non_null_fields) + len(non_zero_fields) + 1  # noqa

    try:
        overall_summation = dataset.groupby(
            location.location_type.name).sum().ix[location.name]
        reported_subset = dataset[dataset.reported == True]     # noqa
        valid_dataframe = reported_subset[
            reported_subset[location.location_type.name] == location.name]
        valid_summation = reported_subset.fillna(0).groupby(
            location.location_type.name).sum().ix[location.name]
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
                    axis=0)),
            'turnout': valid_summation[
                result_field_labels + rejected_votes_field +
                blank_votes_field].sum(axis=0) /
            valid_summation.get(registered_voters_field, 0) or pd.np.inf,
            'all_valid_votes': int(
                valid_summation[result_field_labels].sum(axis=0)),
            'all_valid_votes_pct': valid_summation[result_field_labels].sum(
                axis=0) / valid_summation[result_field_labels +
                                          rejected_votes_field +
                                          blank_votes_field].sum(axis=0),
            'total_rejected': int(valid_summation[rejected_votes_field[0]])
            if rejected_votes_field else 0,
            'total_rejected_pct': valid_summation[rejected_votes_field[0]] /
            valid_summation[
                result_field_labels + rejected_votes_field +
                blank_votes_field].sum(
                axis=0) if rejected_votes_field else 0,
            'total_blanks': int(valid_summation[blank_votes_field[0]])
            if blank_votes_field else 0,
            'total_blanks_pct': valid_summation[blank_votes_field[0]] /
            valid_summation[
                result_field_labels + rejected_votes_field +
                blank_votes_field].sum(
                axis=0) if blank_votes_field else 0
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
        data_analyses['overall']['{}_cnt'.format(result_field_label)] = \
            valid_summation.get(result_field_label, 0) if data_available else 0
        data_analyses['overall']['{}_pct'.format(result_field_label)] = \
            valid_summation.get(result_field_label, 0) / float(
                data_analyses['overall']['all_valid_votes']) \
            if data_available else 0  # all_votes?
        if form.calculate_moe and current_app.config.get('ENABLE_MOE'):
            data_analyses['overall']['{}_moe_95'.format(
                result_field_label)] = _margin_of_error(
                valid_dataframe, result_field_label,
                result_field_labels) \
                if data_available else 0
            data_analyses['overall']['{}_moe_99'.format(
                result_field_label)] = _margin_of_error(
                valid_dataframe, result_field_label,
                result_field_labels, 2.58) \
                if data_available else 0

    # grouped summaries
    for location_type in list(location_tree.keys()):
        data_analyses['grouped'][location_type] = []

        try:
            grouped_summation = dataset.groupby(
                location_type).sum()
            grouped_valid_summation = dataset[
                dataset.reported==True].groupby(location_type).sum()  # noqa

            for sublocation in location_tree[location_type]:
                try:
                    _overall = grouped_summation.ix[sublocation.name]
                    _valid = grouped_valid_summation.fillna(
                        0).ix[sublocation.name]
                    _reported_subset = dataset[dataset.reported==True]  # noqa
                    _valid_dataframe = _reported_subset[
                        _reported_subset[location_type] == sublocation.name]

                    _reporting = _overall[['missing', 'reported']]
                    _reporting['reported_pct'] = _reporting['reported'] / (
                        _reporting['reported'] + _reporting['missing'])
                    _reporting['missing_pct'] = _reporting['missing'] / (
                        _reporting['reported'] + _reporting['missing'])

                    _sublocation_report = {
                        'name': sublocation.name,
                        'location_type': sublocation.location_type.name,
                        'reported_cnt': int(_reporting['reported']),
                        'reported_pct': _reporting['reported_pct'],
                        'missing_cnt': int(_reporting['missing']),
                        'missing_pct': _reporting['missing_pct'],
                        'rv': _valid.get(registered_voters_field, 0),
                        'all_votes': int(
                            _valid[result_field_labels +
                                   rejected_votes_field +
                                   blank_votes_field].sum(
                                axis=0)),
                        'turnout': _valid[
                            result_field_labels + rejected_votes_field +
                            blank_votes_field].sum(
                            axis=0) / _valid.get(
                            registered_voters_field, 0) or pd.np.inf,
                        'all_valid_votes': int(
                            _valid[result_field_labels].sum(axis=0)),
                        'all_valid_votes_pct': _valid[result_field_labels].sum(
                            axis=0) / _valid[result_field_labels +
                                             rejected_votes_field +
                                             blank_votes_field].sum(axis=0),
                        'total_rejected': int(_valid[rejected_votes_field[0]])
                        if rejected_votes_field else 0,
                        'total_rejected_pct': _valid[rejected_votes_field[0]] /
                        _valid[result_field_labels + rejected_votes_field +
                               blank_votes_field].sum(
                            axis=0) if rejected_votes_field else 0,
                        'total_blanks': int(_valid[blank_votes_field[0]])
                        if blank_votes_field else 0,
                        'total_blanks_pct': _valid[blank_votes_field[0]] /
                        _valid[result_field_labels + rejected_votes_field +
                               blank_votes_field].sum(
                            axis=0) if blank_votes_field else 0,
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
                        'location_type': sublocation.location_type.name,
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
                    _sublocation_report['{}_cnt'.format(
                        result_field_label)] = _valid.get(
                        result_field_label, 0) if data_available else 0
                    _sublocation_report['{}_pct'.format(
                        result_field_label)] = _valid.get(
                        result_field_label, 0) / float(
                        _sublocation_report['all_valid_votes']) \
                        if data_available else 0

                    if (
                        form.calculate_moe and current_app.config.get(
                            'ENABLE_MOE')
                    ):
                        _sublocation_report['{}_moe_95'.format(
                            result_field_label)] = _margin_of_error(
                            _valid_dataframe, result_field_label,
                            result_field_labels) \
                            if data_available else 0
                        _sublocation_report['{}_moe_99'.format(
                            result_field_label)] = _margin_of_error(
                            _valid_dataframe, result_field_label,
                            result_field_labels,
                            2.58) if data_available else 0
                data_analyses['grouped'][location_type].append(
                    _sublocation_report)
        except (IndexError, KeyError):
            pass

    if not dataset.empty:
        convergence_dataset = dataset[dataset.reported==True].fillna(0)  # noqa
    else:
        convergence_dataset = pd.DataFrame()

    chart_data = {}

    # restrict the convergence dataframe to result fields and compute the
    # cummulative sum
    if not (dataset.empty and convergence_dataset.empty):
        convergence_df = convergence_dataset.sort_values(
            by='updated')[['updated'] + result_field_labels]
        for field in result_field_labels:
            convergence_df[field] = convergence_df[field].cumsum()

        # compute vote proportions A / (A + B + C + ...)
        convergence_df[result_field_labels] = \
            convergence_df[result_field_labels].div(
                convergence_df[result_field_labels].sum(axis=1), axis=0
            ).fillna(0)

        for component in result_field_labels:
            chart_data[component] = [
                (int(ts_f[0].strftime('%s')) * 1000, ts_f[1] * 100)
                for ts_f in convergence_df[['updated', component]].values]

    breadcrumb_data = analysis_breadcrumb_data(
        form, location, analysis_type='results')
    breadcrumbs.extend([
        {'text': location.name, 'url': url_for(
            'result_analysis.results_analysis_with_location',
            form_id=breadcrumb_data['form'].id,
            location_id=location.id)
         if idx < len(breadcrumb_data.get('locations', [])) - 1 else ''}
        for idx, location in enumerate(breadcrumb_data.get('locations', []))
    ])

    context = {
        'breadcrumbs': breadcrumbs,
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
        'location_tree': location_tree
    }

    return render_template(template_name, **context)


@route(bp, '/results_summary/<form_id>')
@register_menu(
    bp, 'main.analyses.results_analysis',
    _('Results Data'),
    dynamic_list_constructor=partial(get_result_analysis_menu),
    visible_when=lambda: len(get_result_analysis_menu()) > 0
    and permissions.view_result_analysis.can())
@login_required
@permissions.view_result_analysis.require(403)
def results_analysis(form_id):
    return _voting_results(form_id)


@route(bp, '/results_summary/<form_id>/<location_id>')
@login_required
@permissions.view_result_analysis.require(403)
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
