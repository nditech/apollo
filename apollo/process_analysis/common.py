from collections import Counter
from operator import itemgetter
import numpy as np
import pandas as pd


def dataframe_analysis(kind, dataframe, col):
    if kind == 'discrete':
        try:
            result = {
                'value_counts': dict(getattr(dataframe, col).value_counts()),
                'value_counts_sum': getattr(dataframe,
                                            col).value_counts().sum()}
        except AttributeError:
            result = {'value_counts': pd.np.nan, 'value_counts_sum': 0}
    else:
        try:
            result = {'mean': getattr(dataframe, col).mean()}
        except AttributeError:
            result = {'mean': pd.np.nan}

    try:
        result['count'] = getattr(dataframe, col).count()
        result['size'] = getattr(dataframe, col).size
        result['diff'] = result['size'] - result['count']
    except AttributeError:
        result.update({'count': 0, 'size': 0, 'diff': 0})

    return result


def multiselect_dataframe_analysis(dataframe, col, options):
    option_summary = summarize_options(options, dataframe[col])
    result = {
        'value_counts': dict(zip(options, option_summary)),
        'value_counts_sum': dataframe[col].count(),
    }

    result['count'] = dataframe[col].count()
    result['size'] = dataframe[col].size
    result['diff'] = result['size'] - result['count']

    return result


def make_histogram(options, dataset, multi=False):
    '''This function simply returns the number of occurrences of each option
    in the given dataset as a list.

    For example, say options is 'abcde', and dataset is 'capable', it would
    return [2, 1, 1, 0, 1], because there are 2 occurrences of 'a' in
    'capable', 1 of 'b', and so on.

    Please note that both options and dataset must be homogenous iterables
    of the same type.
    '''
    if multi:
        if not isinstance(dataset, list) and pd.isnull(dataset):
            return [0] * len(options)

    counter = Counter(dataset if hasattr(dataset, '__iter__') else [dataset])

    histogram = [counter[option] for option in options]

    return histogram


def summarize_options(options, series):
    '''This function returns a summary of the number of occurrences of each
    option in a pandas Series of lists (although it can be used for any 2D
    iterable).


    For example, if the series contains these lists: [1, 2], [2, 5] and
    [2, 3, 4] and options is [1, 2, 3, 4, 5, 6], it would return
    [1, 3, 1, 1, 1, 0].

    Since this merely uses make_histogram(), the same rules apply.
    '''
    placeholder = []
    for row in series:
        placeholder.append(make_histogram(options, row, True))

    # sum the number of occurrences by column and return as a list
    return np.array(placeholder).sum(axis=0).tolist()


def percent_of(a, b):
    '''Returns the percentage of b that is a'''
    if np.isnan(a) or b == 0:
        return 0
    return float(100 * float(a) / b)


def generate_numeric_field_stats(tag, dataset):
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
    field_stats = {'type': 'numeric'}

    if hasattr(dataset, 'groups'):
        # if we need grouped data, say, by a certain location type, for example
        group_names = dataset.groups.keys()
        group_names.sort()

        # generate the per-group statistics
        # the transpose and to_dict ensures that the output looks similar to
        # ['item']['mean'] for every item in the group
        location_stats = dataset[tag].agg({
            'mean': np.mean,
            'std': lambda x: np.std(x)
        }).replace(np.nan, 0).transpose().to_dict()

        field_stats['locations'] = location_stats

        for group_name in group_names:
            temp = dataset[tag].get_group(group_name)
            total = temp.size
            reported = temp.count()
            missing = total - reported
            percent_reported = percent_of(reported, total)
            percent_missing = percent_of(missing, total)

            field_stats['locations'][group_name]['reported'] = reported
            field_stats['locations'][group_name]['missing'] = missing
            field_stats['locations'][group_name]['percent_reported'] = \
                percent_reported
            field_stats['locations'][group_name]['percent_missing'] = \
                percent_missing

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
                 'mean': dataset[tag].mean(),
                 'std': np.std(dataset[tag])}

        if np.isnan(stats['mean']):
            stats['mean'] = 0

        field_stats.update(stats)

    return field_stats


def generate_single_choice_field_stats(tag, dataset, options, labels=None):
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

    field_stats = {'type': 'single-choice', 'labels': labels}

    if hasattr(dataset, 'groups'):
        # the data is grouped, so per-group statistics will be generated
        group_names = dataset.groups.keys()
        group_names.sort()

        location_stats = {}

        for group_name in group_names:
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

            histogram = make_histogram(options, temp)
            histogram_mod = lambda x: (x, percent_of(x, reported))
            histogram2 = map(histogram_mod, histogram)

            location_stats[group_name]['histogram'] = histogram2

        field_stats['locations'] = location_stats
    else:
        # ungrouped data, statistics for the entire data set will be generated

        reported = dataset[tag].count()
        total = dataset[tag].size
        missing = total - reported
        percent_reported = percent_of(reported, total)
        percent_missing = percent_of(missing, total)

        histogram = make_histogram(options, dataset[tag])
        histogram_mod = lambda x: (x, percent_of(x, reported))
        histogram2 = map(histogram_mod, histogram)

        stats = {'histogram': histogram2, 'reported': reported,
                 'missing': missing, 'percent_reported': percent_reported,
                 'percent_missing': percent_missing,
                 'total': reported + missing}

        field_stats.update(stats)

    return field_stats


def generate_mutiple_choice_field_stats(tag, dataset, options, labels=None):
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
    field_stats = {'type': 'multiple-choice'}

    if hasattr(dataset, 'groups'):
        group_names = dataset.groups.keys()
        group_names.sort()

        field_stats['labels'] = labels
        location_stats = {}

        for group_name in group_names:
            temp = dataset.get_group(group_name).get(tag)

            t = [0 if not isinstance(x, float) and x else 1 for x
                 in temp]
            missing = sum(t)
            reported = temp.size - missing
            total = temp.size
            percent_missing = percent_of(missing, total)
            percent_reported = percent_of(reported, total)

            location_stats[group_name] = {}
            location_stats[group_name]['missing'] = missing
            location_stats[group_name]['reported'] = reported
            location_stats[group_name]['percent_reported'] = percent_reported
            location_stats[group_name]['percent_missing'] = percent_missing

            histogram = summarize_options(options, temp)

            histogram_mod = lambda x: (x, percent_of(x, reported))

            histogram2 = map(histogram_mod, histogram)

            location_stats[group_name]['histogram'] = histogram2

        field_stats['locations'] = location_stats
    else:
        t = [0 if not isinstance(x, float) and x else 1 for x in dataset[tag]]
        missing = sum(t)
        total = dataset[tag].size
        reported = total - missing
        percent_reported = percent_of(reported, total)
        percent_missing = percent_of(missing, total)

        histogram = summarize_options(options, dataset[tag])

        histogram_mod = lambda x: (x, percent_of(x, reported))

        histogram2 = map(histogram_mod, histogram)

        stats = {'histogram': histogram2, 'reported': reported,
                 'missing': missing, 'percent_reported': percent_reported,
                 'percent_missing': percent_missing, 'labels': labels}

        field_stats.update(stats)

    return field_stats


def generate_incident_field_stats(tag, dataset, all_tags, labels=None):
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

    field_stats = {'type': 'incidents', 'labels': labels}

    if hasattr(dataset, 'groups'):
        # the data is grouped, so per-group statistics will be generated
        group_names = dataset.groups.keys()
        group_names.sort()

        location_stats = {}

        for group_name in group_names:
            reported = dataset.get_group(group_name).get(tag).count()
            total = dataset.get_group(group_name).shape[0]
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
        total = dataset.shape[0]
        missing = total - reported

        percent_reported = percent_of(reported, total)
        percent_missing = percent_of(missing, total)

        stats = {'reported': reported,
                 'missing': missing, 'percent_reported': percent_reported,
                 'percent_missing': percent_missing,
                 'total': total}

        field_stats.update(stats)

    return field_stats


def generate_field_stats(field, dataset, all_tags=None):
    ''' In order to simplify the choice on what analysis to perform
    this method will check a few conditions and return the appropriate
    analysis for the field'''
    if field.represents_boolean:
        return generate_incident_field_stats(field.name, dataset, all_tags)

    if field.options:
        sorted_options = sorted(field.options.iteritems(), key=itemgetter(1))
        options = [i[1] for i in sorted_options]
        labels = [i[0] for i in sorted_options]

        if field.allows_multiple_values:
            return generate_mutiple_choice_field_stats(
                field.name, dataset, options=options, labels=labels
            )
        else:
            return generate_single_choice_field_stats(
                field.name, dataset, options=options, labels=labels
            )

    return generate_numeric_field_stats(field.name, dataset)


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
        child.location_type for child in location_root.children()
    }

    if not tags:
        tags = [field.name for group in form.groups for field in group.fields]

    try:
        data_frame = queryset.to_dataframe()

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
                (tag, field.description, field_stats)
            )

        # per-location level summaries
        for location_type in location_types:
            data_group = data_frame.groupby(location_type)
            location_stats = {}

            for tag in tags:
                if tag not in data_frame:
                    continue
                field = form.get_field_by_tag(tag)
                field_stats = generate_field_stats(field, data_group, tags)

                incidents_summary['locations'] = \
                    field_stats['locations'].keys()

                for location in field_stats['locations']:
                    field = form.get_field_by_tag(tag)

                    location_stats.setdefault(location, {}).update({
                        tag: (field.description,
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
        for group in form.groups:
            for field in group.fields:
                if field.name in tags:
                    selected_groups.add(group)

        for group in selected_groups:
            group_summary = []

            for tag in tags:
                if tag not in data_frame:
                    continue
                field = form.get_field_by_tag(tag)
                field_stats = generate_field_stats(field, data_frame, tags)
                group_summary.append((tag, field.description, field_stats))

            sample_summary.append((group.name, group_summary))

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
        child.location_type for child in location_root.children
    }

    if not tags:
        tags = [field.name for group in form.groups for field in group.fields]

    try:
        data_frame = queryset.to_dataframe()

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
                (tag, field.description, field_stats)
            )

        # per-location level summaries
        for location_type in location_types:
            data_group = data_frame.groupby(location_type)
            location_type_summary = []

            for tag in tags:
                if tag not in data_frame:
                    continue
                field = form.get_field_by_tag(tag)
                field_stats = generate_field_stats(field, data_group, tags)

                location_type_summary.append((
                    tag, field.description, field_stats
                ))

            process_summary['groups'].append(
                (location_type, location_type_summary)
            )
    else:
        process_summary['type'] = 'normal'
        sample_summary = []

        selected_groups = set()
        for group in form.groups:
            for field in group.fields:
                if field.name in tags:
                    selected_groups.add(group)

        for group in selected_groups:
            group_summary = []

            for tag in tags:
                if tag not in data_frame:
                    continue
                field = form.get_field_by_tag(tag)
                field_stats = generate_field_stats(field, data_frame, tags)
                group_summary.append((tag, field.description, field_stats))

            sample_summary.append((group.name, group_summary))

        process_summary['summary'] = sample_summary

    return process_summary
