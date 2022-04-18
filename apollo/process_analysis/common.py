# -*- coding: utf-8 -*-
from collections import defaultdict
from functools import partial
from itertools import chain
from operator import itemgetter
import numpy as np
import pandas as pd


def _replace_empty_lists(value):
    if isinstance(value, list) and len(value) == 0:
        return None

    return value


def _fake_cmp(target, value):
    return ((value > target) - (value < target))


def percent_of(a, b):
    '''Returns the percentage of b that is a'''
    if np.isnan(a) or b == 0:
        return 0.0
    return float(100 * float(a) / b)


def generate_mean_stats(tag, dataset, null_value=None):
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
            if null_value is None:
                available = reported
                not_available = 0
                mean = temp.mean()
            else:
                not_available = temp.where(temp == null_value).count()
                available = reported - not_available
                mean = temp[temp != null_value].mean()
            missing = total - reported
            percent_reported = percent_of(reported, total)
            percent_available = percent_of(available, reported)
            percent_not_available = percent_of(not_available, reported)
            percent_missing = percent_of(missing, total)

            location_stats[group_name] = {}
            location_stats[group_name]['reported'] = reported
            location_stats[group_name]['missing'] = missing
            location_stats[group_name]['available'] = available
            location_stats[group_name]['not_available'] = not_available
            location_stats[group_name]['percent_reported'] = \
                percent_reported
            location_stats[group_name]['percent_missing'] = \
                percent_missing
            location_stats[group_name]['percent_available'] = \
                percent_available
            location_stats[group_name]['percent_not_available'] = \
                percent_not_available
            location_stats[group_name]['mean'] = \
                mean if not pd.isnull(mean) else 0.0

        field_stats['locations'] = location_stats
    else:
        # generate the statistics over the entire data set
        # this means there will be one set of statistics for the entire
        # data set, as opposed to above, where each group gets its stats
        # generated separately
        temp = dataset[tag]
        reported = temp.count()
        if null_value is None:
            not_available = 0
            mean = temp.mean()
        else:
            not_available = temp.where(temp == null_value).count()
            mean = temp[temp != null_value].mean()
        total = temp.size
        available = reported - not_available
        missing = total - reported
        percent_reported = percent_of(reported, total)
        percent_missing = percent_of(missing, total)
        percent_available = percent_of(available, reported)
        percent_not_available = percent_of(not_available, reported)

        stats = {
            'reported': reported, 'missing': missing,
            'available': available, 'not_available': not_available,
            'percent_reported': percent_reported,
            'percent_missing': percent_missing,
            'percent_available': percent_available,
            'percent_not_available': percent_not_available,
            'mean': mean
        }

        if np.isnan(stats['mean']):
            stats['mean'] = 0

        field_stats.update(stats)

    return field_stats


def generate_histogram_stats(tag, dataset, options=[], labels=None,
                             null_value=None):
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

    options_generated = set(options)
    if len(options_generated) == 0:
        if hasattr(dataset, 'groups'):
            dataset_slice = pd.concat([subset[tag] for _, subset in dataset])
        else:
            dataset_slice = dataset[tag]
    else:
        if hasattr(dataset, 'groups'):
            dataset_slice = pd.concat([subset[tag] for _, subset in dataset])
        else:
            dataset_slice = dataset[tag]
    options_generated.update(dataset_slice.dropna().unique().astype(int))
    option_labels = sorted(options_generated)

    field_stats = {'type': 'histogram', 'labels': labels}
    descriptors = [
        (l, o) for (l, o) in zip(labels or option_labels, option_labels)
        if o != null_value
    ]
    if null_value in options_generated:
        options_generated.remove(null_value)

    if hasattr(dataset, 'groups'):
        # the data is grouped, so per-group statistics will be generated
        location_stats = {}

        for group_name in dataset.groups:
            temp = dataset.get_group(group_name).get(tag)

            reported = temp.count()
            if null_value is None:
                not_available = 0
            else:
                not_available = temp.where(temp == null_value).count()
            available = reported - not_available
            total = temp.size
            missing = total - reported
            percent_reported = percent_of(reported, total)
            percent_available = percent_of(available, reported)
            percent_not_available = percent_of(not_available, reported)
            percent_missing = percent_of(missing, total)

            location_stats[group_name] = {}
            location_stats[group_name]['missing'] = missing
            location_stats[group_name]['reported'] = reported
            location_stats[group_name]['available'] = available
            location_stats[group_name]['not_available'] = not_available
            location_stats[group_name]['total'] = reported + missing
            location_stats[group_name]['percent_reported'] = percent_reported
            location_stats[group_name]['percent_missing'] = percent_missing
            location_stats[group_name]['percent_available'] = percent_available
            location_stats[group_name]['percent_not_available'] = \
                percent_not_available

            subset = temp if null_value is None else temp[temp != null_value]
            value_counts = subset.dropna().astype(int).value_counts().to_dict()

            histogram = defaultdict(lambda: (0, 0.0))
            denominator = reported if null_value is None else available
            histogram = {
                opt: (
                    value_counts.get(opt, 0),
                    percent_of(value_counts.get(opt, 0), denominator)
                )
                for opt in options_generated
            }

            location_stats[group_name]['histogram'] = histogram

        field_stats['locations'] = location_stats
    else:
        # ungrouped data, statistics for the entire data set will be generated
        temp = dataset[tag]
        subset = temp if null_value is None else temp[temp != null_value]
        reported = temp.count()
        if null_value is None:
            not_available = 0
        else:
            not_available = temp.where(temp == null_value).count()

        available = reported - not_available
        total = temp.size
        missing = total - reported
        percent_reported = percent_of(reported, total)
        percent_missing = percent_of(missing, total)
        percent_available = percent_of(available, reported)
        percent_not_available = percent_of(not_available, reported)

        value_counts = subset.dropna().astype(
            int).value_counts().to_dict()
        histogram = defaultdict(lambda: (0, 0.0))
        denominator = reported if null_value is None else available
        histogram = {
            opt: (
                value_counts.get(opt, 0),
                percent_of(value_counts.get(opt, 0), denominator)
            )
            for opt in options_generated
        }

        stats = {
            'histogram': histogram, 'reported': reported,
            'missing': missing, 'percent_reported': percent_reported,
            'percent_missing': percent_missing,
            'percent_available': percent_available,
            'percent_not_available': percent_not_available,
            'total': total, 'available': available,
            'not_available': not_available,
        }

        field_stats.update(stats)

    option_labels = sorted(options_generated)
    field_stats.update(meta=descriptors)

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
            histogram = defaultdict(lambda: (0, 0.0))
            histogram = {
                opt: (
                    value_counts.get(opt, 0),
                    percent_of(value_counts.get(opt, 0), reported)
                )
                for opt in options
            }

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
        histogram = defaultdict(lambda: (0, 0.0))
        histogram = {
            opt: (
                value_counts.get(opt, 0),
                percent_of(value_counts.get(opt, 0), reported)
            )
            for opt in options
        }

        stats = {
            'histogram': histogram, 'reported': reported,
            'missing': missing, 'percent_reported': percent_reported,
            'percent_missing': percent_missing
        }

        field_stats.update(stats)

    field_stats.update(meta=list(zip(labels or [], options)))

    return field_stats


def generate_count_stats(tag, dataset, null_value=None):
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
            subset = dataset.get_group(group_name).get(tag)
            reported = subset.count()
            if null_value is None:
                not_available = 0
            else:
                not_available = subset.where(subset == null_value).count()
            total = subset.size
            missing = total - reported
            available = reported - not_available

            percent_reported = percent_of(reported, total)
            percent_missing = percent_of(missing, total)
            percent_available = percent_of(available, reported)
            percent_not_available = percent_of(not_available, reported)

            location_stats[group_name] = {}
            location_stats[group_name]['missing'] = missing
            location_stats[group_name]['reported'] = reported
            location_stats[group_name]['available'] = available
            location_stats[group_name]['not_available'] = not_available
            location_stats[group_name]['total'] = total
            location_stats[group_name]['percent_reported'] = percent_reported
            location_stats[group_name]['percent_missing'] = percent_missing
            location_stats[group_name]['percent_available'] = percent_available
            location_stats[group_name]['percent_not_available'] = \
                percent_not_available

        field_stats['locations'] = location_stats
    else:
        # ungrouped data, statistics for the entire data set will be generated
        subset = dataset[tag]
        reported = subset.count()
        if null_value is None:
            not_available = 0
        else:
            not_available = subset.where(subset == null_value).count()
        available = reported - not_available
        total = subset.size
        missing = total - reported

        percent_reported = percent_of(reported, total)
        percent_missing = percent_of(missing, total)
        percent_available = percent_of(available, reported)
        percent_not_available = percent_of(not_available, reported)

        stats = {
            'reported': reported,
            'missing': missing,
            'available': available,
            'not_available': not_available,
            'percent_reported': percent_reported,
            'percent_missing': percent_missing,
            'percent_available': percent_available,
            'percent_not_available': percent_not_available,
            'total': total,
        }

        field_stats.update(stats)

    return field_stats


def generate_bucket_stats(tag, dataset, target, null_value=None):
    _cmp = partial(_fake_cmp, target)
    field_stats = {'type': 'bucket', 'target': target}
    options = [-1, 0, 1]

    if hasattr(dataset, 'groups'):
        location_stats = {}

        for group_name in dataset.groups:
            column_data = dataset.get_group(group_name)[tag]
            if null_value is None:
                transformed_data = column_data.dropna().apply(_cmp)
                not_available = 0
            else:
                transformed_data = column_data[
                    column_data != null_value].dropna().apply(_cmp)
                not_available = column_data.where(
                    column_data == null_value).count()
            value_counts = transformed_data.value_counts().to_dict()
            reported = column_data.count()
            total = column_data.size
            missing = total - reported
            available = reported - not_available
            percent_reported = percent_of(reported, total)
            percent_missing = percent_of(missing, total)
            percent_available = percent_of(available, reported)
            percent_not_available = percent_of(not_available, reported)
            histogram = defaultdict(lambda: (0, 0.0))
            histogram = {
                opt: (
                    value_counts.get(opt, 0),
                    percent_of(value_counts.get(opt, 0), reported)
                )
                for opt in options
            }

            location_stats[group_name] = {}
            location_stats[group_name]['missing'] = missing
            location_stats[group_name]['reported'] = reported
            location_stats[group_name]['available'] = available
            location_stats[group_name]['not_available'] = not_available
            location_stats[group_name]['total'] = total
            location_stats[group_name]['percent_reported'] = percent_reported
            location_stats[group_name]['percent_available'] = percent_available
            location_stats[group_name]['percent_not_available'] = \
                percent_not_available
            location_stats[group_name]['percent_missing'] = percent_missing
            location_stats[group_name]['histogram'] = histogram

        field_stats['locations'] = location_stats
    else:
        column_data = dataset[tag]
        if null_value is None:
            transformed_data = column_data.dropna().apply(_cmp)
            not_available = 0
        else:
            transformed_data = column_data[
                column_data != null_value].dropna().apply(_cmp)
            not_available = column_data.where(
                column_data == null_value).count()
        value_counts = transformed_data.value_counts().to_dict()
        reported = column_data.count()
        available = reported - not_available
        total = column_data.size
        missing = total - reported
        percent_reported = percent_of(reported, total)
        percent_missing = percent_of(missing, total)
        percent_available = percent_of(available, reported)
        percent_not_available = percent_of(not_available, reported)
        histogram = defaultdict(lambda: (0, 0.0))
        histogram = {
            opt: (
                value_counts.get(opt, 0),
                percent_of(value_counts.get(opt, 0), reported)
            )
            for opt in options
        }

        stats = {
            'histogram': histogram, 'reported': reported,
            'missing': missing, 'percent_reported': percent_reported,
            'percent_missing': percent_missing,
            'percent_available': percent_available,
            'percent_not_available': percent_not_available,
        }

        field_stats.update(stats)

    return field_stats


def generate_field_stats(field, dataset):
    ''' In order to simplify the choice on what analysis to perform
    this method will check a few conditions and return the appropriate
    analysis for the field'''
    summary_type = field.get('analysis_type')
    try:
        null_value = int(field.get('null_value'))
    except (TypeError, ValueError):
        null_value = None
    if summary_type == 'count':
        return generate_count_stats(field['tag'], dataset, null_value)

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
                field['tag'], dataset, options=options, labels=labels,
            )
        else:
            return generate_histogram_stats(
                field['tag'], dataset, options=options, labels=labels,
                null_value=null_value,
            )

    if summary_type == 'mean':
        return generate_mean_stats(
            field['tag'], dataset, null_value=null_value)

    if summary_type == 'bucket':
        return generate_bucket_stats(
            field['tag'], dataset, field.get('expected', 0),
            null_value=null_value)


def generate_incidents_data(data_frame, form, location_root, grouped=True,
                            tags=None):
    '''Generates process statistics for either a location and its descendants,
    or for a sample. Optionally generates statistics for an entire region, or
    for groups of regions.

    Parameters
    - data_frame: a dataframe of submission data
                  (generated from `make_submission_dataframe`)
    - form: a Form instance
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

    if data_frame.empty:
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
            field_stats = generate_field_stats(field, data_frame)
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
                field_stats = generate_field_stats(field, data_group)

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
                field_stats = generate_field_stats(field, data_frame)
                group_summary.append((tag, field['description'], field_stats))

            sample_summary.append((group['name'], group_summary))

        incidents_summary['summary'] = sample_summary

    return incidents_summary


def generate_process_data(data_frame, form, location_root, grouped=True,
                          tags=None):
    '''Generates process statistics for either a location and its descendants,
    or for a sample. Optionally generates statistics for an entire region, or
    for groups of regions.

    Parameters
    - data_frame: a dataframe of submission data
                  (generated from `make_submission_dataframe`)
    - form: a Form instance
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

    if data_frame.empty:
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
            field_stats = generate_field_stats(field, data_frame)

            process_summary['top'].append(
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
            location_type_summary = []

            for tag in tags:
                if tag not in data_frame:
                    continue
                field = form.get_field_by_tag(tag)
                field_stats = generate_field_stats(field, data_group)

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
                field_stats = generate_field_stats(field, data_frame)
                group_summary.append((tag, field['description'], field_stats))

            sample_summary.append((group['name'], group_summary))

        process_summary['summary'] = sample_summary

    return process_summary
