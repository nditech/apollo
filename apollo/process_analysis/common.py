# -*- coding: utf-8 -*-
from collections import defaultdict
from functools import partial
from itertools import chain
from operator import itemgetter
import numpy as np
import pandas as pd

from apollo.submissions.utils import make_submission_dataframe


def _default_zero():
    return 0


def _replace_empty_lists(value):
    if isinstance(value, list) and len(value) == 0:
        return None

    return value


def _fake_cmp(target, value):
    return ((value > target) - (value < target))


def percent_of(a, b):
    '''Returns the percentage of b that is a'''
    if np.isnan(a) or b == 0:
        return 0
    return float(100 * float(a) / b)


def generate_mean_stats(tag, dataset):
    '''Returns statistics (mean, standard deviation, number/percentage
    of actual reports, number/percentage of missing reports) for a
    single form field tag in a set of submissions.


    Parameters:
    - tag: a form field tag.
    - dataset: a pandas DataFrame or group series with the submission data

    Returns
    - a dictionary of the requested statistics. if the dataset is a series
    group, the result will be a nested dictionary
    '''
    field_stats = {'type': 'mean'}

    if hasattr(dataset, 'groups'):
        # generate the per-group statistics
        # the transpose and to_dict ensures that the output looks similar to
        # ['item']['mean'] for every item in the group
        # location_stats = dataset[tag].agg({
        #     'mean': np.mean,
        #     'std': lambda x: np.std(x)
        # }).replace(np.nan, 0).transpose().to_dict()
        location_stats = {}

        for group_name in dataset.groups:
            temp = dataset[tag].get_group(group_name)
            total = temp.size
            reported = temp.count()
            missing = total - reported
            percent_reported = percent_of(reported, total)
            percent_missing = percent_of(missing, total)

            location_stats[group_name] = {}
            location_stats[group_name]['reported'] = reported
            location_stats[group_name]['missing'] = missing
            location_stats[group_name]['percent_reported'] = \
                percent_reported
            location_stats[group_name]['percent_missing'] = \
                percent_missing
            mean = temp.mean()
            location_stats[group_name]['mean'] = \
                mean if not pd.isnull(mean) else 0

        field_stats['locations'] = location_stats
    else:
        # generate the statistics over the entire data set
        # this means there will be one set of statistics for the entire
        # data set, as opposed to above, where each group gets its stats
        # generated separately
        reported = dataset[tag].count()
        total = dataset[tag].size
        missing = total - reported
        percent_reported = percent_of(reported, total)
        percent_missing = percent_of(missing, total)

        stats = {'reported': reported, 'missing': missing,
                 'percent_reported': percent_reported,
                 'percent_missing': percent_missing,
                 'mean': dataset[tag].mean()}

        if np.isnan(stats['mean']):
            stats['mean'] = 0

        field_stats.update(stats)

    return field_stats


def generate_histogram_stats(tag, dataset, options=[], labels=None):
    '''Returns statistics (frequency histogram, number/percentage of actual
    reports, number/percentage of missing reports) for a specified form field
    tag. The associated form field takes one value of several options.


    Parameters
    - tag: a form field tag
    - dataset: a pandas DataFrame or group series with the submission data
    - options: an iterable (queryset or no) of form field options

    Returns
    - a dictionary (or nested dictionary, if data set is grouped) with the
    above statistics, as well as the labels for each of the options. Both the
    histogram and the labels are generated as lists, so they are ordered.'''

    options_generated = set()

    field_stats = {'type': 'histogram', 'labels': labels}

    if hasattr(dataset, 'groups'):
        # the data is grouped, so per-group statistics will be generated
        location_stats = {}

        for group_name in dataset.groups:
            temp = dataset.get_group(group_name).get(tag)

            reported = temp.count()
            total = temp.size
            missing = total - reported
            percent_reported = percent_of(reported, total)
            percent_missing = percent_of(missing, total)

            location_stats[group_name] = {}
            location_stats[group_name]['missing'] = missing
            location_stats[group_name]['reported'] = reported
            location_stats[group_name]['total'] = reported + missing
            location_stats[group_name]['percent_reported'] = percent_reported
            location_stats[group_name]['percent_missing'] = percent_missing

            value_counts = temp.dropna().astype(int).value_counts().to_dict()
            if not options:
                options_generated.update(value_counts.keys())
            group_opts = options or sorted(options_generated)

            histogram = [
                (
                    value_counts.get(opt, 0),
                    percent_of(value_counts.get(opt, 0), reported)
                )
                for opt in group_opts
            ]

            location_stats[group_name]['histogram'] = histogram

        field_stats['locations'] = location_stats
    else:
        # ungrouped data, statistics for the entire data set will be generated

        reported = dataset[tag].count()
        total = dataset[tag].size
        missing = total - reported
        percent_reported = percent_of(reported, total)
        percent_missing = percent_of(missing, total)

        value_counts = dataset[tag].dropna().astype(
            int).value_counts().to_dict()
        if not options:
            options_generated.update(value_counts.keys())
        opts = options or sorted(options_generated)
        histogram = [
            (
                value_counts.get(opt, 0),
                percent_of(value_counts.get(opt, 0), reported)
            )
            for opt in opts
        ]

        stats = {'histogram': histogram, 'reported': reported,
                 'missing': missing, 'percent_reported': percent_reported,
                 'percent_missing': percent_missing,
                 'total': reported + missing}

        field_stats.update(stats)

    options = options if options else sorted(options_generated)
    field_stats.update(meta=list(zip(labels or [], options)))

    return field_stats


def generate_multiselect_histogram_stats(tag, dataset, options, labels=None):
    '''Returns statistics for a form field which can take more than one
    option of several. Statistics returned are frequency histogram,
    number/percentage of actual reports, number/percentage of missing
    reports.

    Parameters
    - tag: a form field tag
    - dataset: a pandas DataFrame or group series
    - field_options: an iterable of form field options

    Returns
    - a dictionary (nested in the case of dataset being a group series)
    of the relevant statistics.'''
    field_stats = {'type': 'histogram', 'labels': labels}

    if hasattr(dataset, 'groups'):
        location_stats = {}

        for group_name in dataset.groups:
            temp = dataset.get_group(group_name).get(tag).apply(
                _replace_empty_lists)
            flattened_data = pd.Series(list(chain(*temp.dropna().values)))
            reported = temp.count()
            total = temp.size
            missing = total - reported
            percent_missing = percent_of(missing, total)
            percent_reported = percent_of(reported, total)

            location_stats[group_name] = {}
            location_stats[group_name]['missing'] = missing
            location_stats[group_name]['reported'] = reported
            location_stats[group_name]['percent_reported'] = percent_reported
            location_stats[group_name]['percent_missing'] = percent_missing

            value_counts = flattened_data.value_counts()
            histogram = [
                (
                    value_counts.get(opt, 0),
                    percent_of(value_counts.get(opt, 0), reported)
                )
                for opt in options
            ]

            location_stats[group_name]['histogram'] = histogram

        field_stats['locations'] = location_stats
    else:
        column_data = dataset[tag].apply(_replace_empty_lists)
        flattened_column_data = pd.Series(
            list(chain(*column_data.dropna().values)))
        reported = column_data.count()
        total = column_data.size
        missing = total - reported
        percent_reported = percent_of(reported, total)
        percent_missing = percent_of(missing, total)

        value_counts = flattened_column_data.value_counts()
        histogram = [
            (
                value_counts.get(opt, 0),
                percent_of(value_counts.get(opt, 0), reported)
            )
            for opt in options
        ]

        stats = {'histogram': histogram, 'reported': reported,
                 'missing': missing, 'percent_reported': percent_reported,
                 'percent_missing': percent_missing}

        field_stats.update(stats)

    field_stats.update(meta=list(zip(labels or [], options)))

    return field_stats


def generate_count_stats(tag, dataset):
    '''Returns statistics (frequency histogram, number/percentage of actual
    reports, number/percentage of missing reports) for a specified form field
    tag. The associated form field takes one value of several options.


    Parameters
    - tag: a form field tag
    - dataset: a pandas DataFrame or group series with the submission data

    Returns
    - a dictionary (or nested dictionary, if data set is grouped) with the
    above statistics, as well as the labels for each of the options. Both the
    histogram and the labels are generated as lists, so they are ordered.'''

    field_stats = {'type': 'count'}

    if hasattr(dataset, 'groups'):
        # the data is grouped, so per-group statistics will be generated
        location_stats = {}

        for group_name in dataset.groups:
            reported = dataset.get_group(group_name).get(tag).count()
            total = dataset[tag].get_group(group_name).size
            missing = total - reported

            percent_reported = percent_of(reported, total)
            percent_missing = percent_of(missing, total)

            location_stats[group_name] = {}
            location_stats[group_name]['missing'] = missing
            location_stats[group_name]['reported'] = reported
            location_stats[group_name]['total'] = total
            location_stats[group_name]['percent_reported'] = percent_reported
            location_stats[group_name]['percent_missing'] = percent_missing

        field_stats['locations'] = location_stats
    else:
        # ungrouped data, statistics for the entire data set will be generated

        reported = dataset[tag].count()
        total = dataset[tag].size
        missing = total - reported

        percent_reported = percent_of(reported, total)
        percent_missing = percent_of(missing, total)

        stats = {'reported': reported,
                 'missing': missing, 'percent_reported': percent_reported,
                 'percent_missing': percent_missing,
                 'total': total}

        field_stats.update(stats)

    return field_stats


def generate_bucket_stats(tag, dataset, target):
    _cmp = partial(_fake_cmp, target)
    field_stats = {'type': 'bucket'}

    if hasattr(dataset, 'groups'):
        location_stats = {}

        for group_name in dataset.groups:
            column_data = dataset.get_group(group_name)[tag]
            transformed_data = column_data.dropna().apply(_cmp)
            value_counts = transformed_data.value_counts().to_dict()
            reported = column_data.count()
            total = column_data.size
            missing = total - reported
            percent_reported = percent_of(reported, total)
            percent_missing = percent_of(missing, total)
            histogram = [
                (r[1], percent_of(r[1], reported))
                for r in sorted(value_counts.items(), key=itemgetter(0))
            ]

            location_stats[group_name] = {}
            location_stats[group_name]['missing'] = missing
            location_stats[group_name]['reported'] = reported
            location_stats[group_name]['total'] = total
            location_stats[group_name]['percent_reported'] = percent_reported
            location_stats[group_name]['percent_missing'] = percent_missing
            location_stats[group_name]['histogram'] = histogram

        field_stats['locations'] = location_stats
    else:
        column_data = dataset[tag]
        transformed_data = column_data.dropna().apply(_cmp)
        value_counts = transformed_data.value_counts().to_dict()
        reported = column_data.count()
        total = column_data.size
        missing = total - reported
        percent_reported = percent_of(reported, total)
        percent_missing = percent_of(missing, total)
        histogram = [
            (r[1], percent_of(r[1], reported))
            for r in sorted(value_counts.items(), key=itemgetter(0))
        ]

        stats = {
            'histogram': histogram, 'reported': reported,
            'missing': missing, 'percent_reported': percent_reported,
            'percent_missing': percent_missing
        }

        field_stats.update(stats)

    return field_stats


def generate_field_stats(field, dataset, all_tags=None):
    ''' In order to simplify the choice on what analysis to perform
    this method will check a few conditions and return the appropriate
    analysis for the field'''
    summary_type = field.get('analysis_type')
    if summary_type == 'count':
        return generate_count_stats(field['tag'], dataset)

    if summary_type == 'histogram':
        field_options = field.get('options')
        if field_options:
            sorted_options = sorted(field_options.items(), key=itemgetter(1))
            options = [i[1] for i in sorted_options]
            labels = [i[0] for i in sorted_options]
        else:
            options = []
            labels = None

        if field['type'] == 'multiselect':
            return generate_multiselect_histogram_stats(
                field['tag'], dataset, options=options, labels=labels
            )
        else:
            return generate_histogram_stats(
                field['tag'], dataset, options=options, labels=labels
            )

    if summary_type == 'mean':
        return generate_mean_stats(field['tag'], dataset)

    if summary_type == 'bucket':
        return generate_bucket_stats(field['tag'], dataset, field['expected'])


def generate_incidents_data(form, queryset, location_root, grouped=True,
                            tags=None):
    '''Generates process statistics for either a location and its descendants,
    or for a sample. Optionally generates statistics for an entire region, or
    for groups of regions.

    Parameters
    - form: a Form instance
    - queryset: a queryset of submissions
    - location_root: a root location to retrieve statistics for
    - grouped: when retrieving statistics for a location, specify whether or
    not to retrieve statistics on a per-group basis.
    - tags: an iterable of tags to retrieve statistics for'''
    incidents_summary = {}

    location_types = {
        child.name for child in location_root.location_type.children()
    }

    if not tags:
        tags = [
            field['tag'] for group in form.data['groups']
            for field in group['fields']
            if field['analysis_type'] != 'N/A'
        ]

    try:
        data_frame = make_submission_dataframe(queryset, form)

        if data_frame.empty:
            return incidents_summary
    except Exception:
        return incidents_summary

    if grouped:
        if not location_types:
            return incidents_summary

        incidents_summary['type'] = 'grouped'
        incidents_summary['groups'] = []
        incidents_summary['locations'] = set()
        incidents_summary['top'] = []
        incidents_summary['tags'] = tags

        # top level summaries
        for tag in tags:
            if tag not in data_frame:
                continue
            field = form.get_field_by_tag(tag)
            field_stats = generate_field_stats(field, data_frame, tags)
            field = form.get_field_by_tag(tag)

            incidents_summary['top'].append(
                (tag, field['description'], field_stats)
            )

        # per-location level summaries
        for location_type in location_types:
            try:
                if location_type not in data_frame.columns:
                    continue
                data_group = data_frame.groupby(location_type)
            except KeyError:
                continue
            location_stats = {}

            for tag in tags:
                if tag not in data_frame:
                    continue
                field = form.get_field_by_tag(tag)
                field_stats = generate_field_stats(field, data_group, tags)

                incidents_summary['locations'] = \
                    list(field_stats['locations'].keys())

                for location in field_stats['locations']:
                    field = form.get_field_by_tag(tag)

                    location_stats.setdefault(location, {}).update({
                        tag: (field['description'],
                              field_stats['locations'][location])})

            group_location_stats = [
                (location, location_stats[location])
                for location in sorted(location_stats.keys())
            ]
            incidents_summary['groups'].append((location_type,
                                                group_location_stats))
    else:
        incidents_summary['type'] = 'normal'
        sample_summary = []

        selected_groups = set()
        for group in form.data['groups']:
            for field in group['fields']:
                if field['tag'] in tags:
                    selected_groups.add(group)

        for group in selected_groups:
            group_summary = []

            for tag in tags:
                if tag not in data_frame:
                    continue
                field = form.get_field_by_tag(tag)
                field_stats = generate_field_stats(field, data_frame, tags)
                group_summary.append((tag, field['description'], field_stats))

            sample_summary.append((group['name'], group_summary))

        incidents_summary['summary'] = sample_summary

    return incidents_summary


def generate_process_data(form, queryset, location_root, grouped=True,
                          tags=None):
    '''Generates process statistics for either a location and its descendants,
    or for a sample. Optionally generates statistics for an entire region, or
    for groups of regions.

    Parameters
    - form: a Form instance
    - queryset: a queryset of submissions
    - location_root: a root location to retrieve statistics for
    - grouped: when retrieving statistics for a location, specify whether or
    not to retrieve statistics on a per-group basis.
    - tags: an iterable of tags to retrieve statistics for'''
    process_summary = {}

    location_types = {
        child.name for child in location_root.location_type.children()
    }

    if not tags:
        tags = [
            field['tag'] for group in form.data['groups']
            for field in group['fields']
            if field['analysis_type'] != 'N/A'
        ]

    try:
        data_frame = make_submission_dataframe(queryset, form)

        if data_frame.empty:
            return process_summary
    except Exception:
        return process_summary

    if grouped:
        if not location_types:
            return process_summary

        process_summary['type'] = 'grouped'
        process_summary['groups'] = []
        process_summary['top'] = []

        # top level summaries
        for tag in tags:
            if tag not in data_frame:
                continue
            field = form.get_field_by_tag(tag)
            field_stats = generate_field_stats(field, data_frame, tags)

            process_summary['top'].append(
                (tag, field['description'], field_stats)
            )

        # per-location level summaries
        for location_type in location_types:
            try:
                if location_type in data_frame.columns:
                    continue
                data_group = data_frame.groupby(location_type)
            except KeyError:
                continue
            location_type_summary = []

            for tag in tags:
                if tag not in data_frame:
                    continue
                field = form.get_field_by_tag(tag)
                field_stats = generate_field_stats(field, data_group, tags)

                location_type_summary.append((
                    tag, field['description'], field_stats
                ))

            process_summary['groups'].append(
                (location_type, location_type_summary)
            )
    else:
        process_summary['type'] = 'normal'
        sample_summary = []

        selected_groups = set()
        for group in form.data['groups']:
            for field in group['fields']:
                if field['tag'] in tags:
                    selected_groups.add(group)

        for group in selected_groups:
            group_summary = []

            for tag in tags:
                if tag not in data_frame:
                    continue
                field = form.get_field_by_tag(tag)
                field_stats = generate_field_stats(field, data_frame, tags)
                group_summary.append((tag, field['description'], field_stats))

            sample_summary.append((group['name'], group_summary))

        process_summary['summary'] = sample_summary

    return process_summary
