from collections import Counter
import numpy as np
import pandas as pd
from core.models import *


def make_histogram(options, dataset):
    '''This function simply returns the number of occurrences of each option
    in the given dataset as a list.

    For example, say options is 'abcde', and dataset is 'capable', it would
    return [2, 1, 1, 0, 1], because there are 2 occurrences of 'a' in
    'capable', 1 of 'b', and so on.

    Please note that both options and dataset must be homogenous iterables
    of the same type.
    '''
    counter = Counter(dataset)

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
        placeholder.append(make_histogram(options, row))

    # sum the number of occurrences by column and return as a list
    return np.array(placeholder).sum(axis=0).tolist()


def get_data_records(form, qs, location_root=None, tags=None):
    '''
    Given a form model instance and a queryset, generate a pandas DataFrame
    containing the submitted form values for locations below the specified
    location_root.
    '''
    if not tags:
        # fields that can store multiple variables are to be handled differently
        _all = FormField.objects.filter(group__form=form).values('tag', 'allow_multiple')
        multivariate_fields = map(lambda x: x['tag'], filter(lambda x: x['allow_multiple'], _all))
        regular_fields = map(lambda x: x['tag'], filter(lambda x: not x['allow_multiple'], _all))
        all_fields = multivariate_fields + regular_fields
    else:
        _all = FormField.objects.filter(group__form=form, tag__in=tags).values('tag', 'allow_multiple')
        multivariate_fields = map(lambda x: x['tag'], filter(lambda x: x['allow_multiple'], _all))
        regular_fields = map(lambda x: x['tag'], filter(lambda x: not x['allow_multiple'], _all))
        all_fields = multivariate_fields + regular_fields

    if not location_root:
        location_root = Location.root()

    # retrieve all child location types for this location
    location_types = [lt.name for lt in location_root.sub_location_types()]

    # in addition to retrieving field data, also retrieve the location_id
    submissions = list(qs.data(all_fields).values(*(['location_id'] + all_fields)))
    locations_graph = get_locations_graph()

    for submission in submissions:
        '''
        Annotate the submissions with their ancestral location data as specified by `location_types`
        '''
        if location_types:
            ancestor_locations = get_location_ancestors_by_type(locations_graph, submission['location_id'], location_types)
            for ancestor_location in ancestor_locations:
                submission[ancestor_location['type']] = ancestor_location['name']

        # for numerical processing, we need to convert the responses into integers
        # note also that multivariates are converted into a list non numeric values
        # are represented as NaNs
        for _field in regular_fields:
            submission[_field] = int(submission[_field]) if submission[_field] else pd.np.nan
        for _field in multivariate_fields:
            submission[_field] = map(lambda x: int(x) if x else pd.np.nan, submission[_field].split(",") if submission[_field] else [])

    return (pd.DataFrame(submissions), regular_fields, multivariate_fields)


def percent_of(a, b):
    '''Returns the percentage of b that is a'''
    if np.isnan(a) or b == 0:
        return 0
    return (100 * float(a) / b)


def get_numeric_field_stats(tag, data_frame, groups):
    '''Generates statistics (mean, sample standard deviation) for a FormField
    which takes a numeric value. Generates both per-group and dataset-wide
    statistics. Also generates report statistics.

    Parameters
    - tag: a submission field tag
    - data_frame: a pandas DataFrame containing the submission data, generated
    using get_data_records()
    - groups: a list of group names used for grouping the data
    '''
    field_stats = {'type': 'numeric', 'group_stats': [], 'regional_stats': {}}

    # return immediately if there are no data
    if data_frame.empty:
        return field_stats

    # iterate over each group, and perform the statistic calculations needed
    for group in groups:

        # skip groups not contained in data frame
        if not group in data_frame:
            continue

        group_stats = {}

        data_group = data_frame.groupby(group)

        # transpose (matrix operation) to swap columns and rows
        group_stats = data_group[tag].agg({'mean': np.mean,
            'std': lambda x: np.std(x)}).replace(np.nan, 0, inplace=True).transpose().to_dict()

        group_names = data_group.groups.keys()

        # calculated report statistics
        for group_name in group_names:
            named_group = data_group[tag].get_group(group_name)
            total = named_group.size
            reported = named_group.count()
            missing = total - reported
            percent_reported = percent_of(reported, total)
            percent_missing = percent_of(missing, total)

            group_stats[group_name]['missing'] = (missing, percent_missing)
            group_stats[group_name]['reported'] = (reported, percent_reported)

        field_stats['group_stats'].append({group: group_stats})

        # calculate regional stats
        regional_mean = data_frame[tag].mean()
        regional_std = np.std(data_frame[tag])

        if np.isnan(regional_mean):
            regional_mean = 0

        field_stats['regional_stats']['mean'] = regional_mean
        field_stats['regional_stats']['std'] = regional_std

    return field_stats


def get_single_choice_field_stats(tag, data_frame, groups, field_options):
    '''Generates statistics (frequency histogram, report statistics) for
    a form field which takes a single option of several.
    '''

    field_stats = {'type': 'single-choice', 'group_stats': [], 'regional_stats': {}}
    labels = [x.description for x in field_options]
    options = [x.option for x in field_options]

    if data_frame.empty:
        return field_stats

    # group the data frame by each supplied group, and generate the stats
    # for each
    for group in groups:

        # skip if the group does not exist
        if not group in data_frame:
            continue

        group_stats = []

        data_group = data_frame.groupby(group)

        group_names = data_group.groups.keys()
        group_names.sort()

        for group_name in group_names:
            named_group = data_group[tag].get_group(group_name)

            reported = named_group.count()
            total = named_group.size
            missing = total - reported

            percent_reported = percent_of(reported, total)
            percent_missing = percent_of(missing, total)

            # generate frequency histogram
            histogram = make_histogram(options, named_group)

            # remap histogram so it has percentage of total as well
            f = lambda x: (x, percent_of(x, reported))

            frequency_pairs = map(f, histogram)

            group_stats.append({group_name: {'histogram': frequency_pairs,
                'reported': (reported, percent_reported),
                'missing': (missing, percent_missing)}})

        field_stats['group_stats'].append({group: group_stats})

    # get regional histogram
    regional_total = data_frame[tag].size
    regional_reported = data_frame[tag].count()
    # regional_missing = regional_total - regional_reported
    regional_histogram = make_histogram(options, data_frame[tag])

    f = lambda x: (x, percent_of(x, regional_reported))

    regional_frequency_pairs = map(f, regional_histogram)

    field_stats['regional_stats'] = {'histogram': regional_frequency_pairs}
    field_stats['labels'] = labels

    return field_stats


def get_multiple_choice_field_stats(tag, data_frame, groups, field_options):
    '''Generates statistics (frequency histogram, report statistics) for
    a form field which takes any number of several options.
    '''

    field_stats = {'type': 'multiple-choice', 'group_stats': [], 'regional_stats': {}}
    labels = [x.description for x in field_options]
    options = [x.option for x in field_options]

    if data_frame.empty:
        return field_stats

    # group the data frame by each supplied group, and generate the stats
    # for each
    for group in groups:

        # skip if the group does not exist
        if not group in data_frame:
            continue

        group_stats = []

        data_group = data_frame.groupby(group)

        group_names = data_group.groups.keys()
        group_names.sort()

        for group_name in group_names:
            named_group = data_group[tag].get_group(group_name)

            total = named_group.size
            missing = sum(not x for x in named_group)
            reported = total - missing

            percent_reported = percent_of(reported, total)
            percent_missing = percent_of(missing, total)

            # generate frequency histogram
            histogram = summarize_options(options, named_group)

            # remap histogram so it has percentage of total as well
            f = lambda x: (x, percent_of(x, total))

            frequency_pairs = map(f, histogram)

            group_stats.append({group_name: {'histogram': frequency_pairs,
                'reported': (reported, percent_reported),
                'missing': (missing, percent_missing)}})

        field_stats['group_stats'].append({group: group_stats})

    # get regional histogram
    regional_total = data_frame[tag].size
    regional_missing = sum(not x for x in data_frame[tag])
    regional_reported = regional_total - regional_missing
    regional_histogram = summarize_options(options, data_frame[tag])

    f = lambda x: (x, percent_of(x, regional_total))

    regional_frequency_pairs = map(f, regional_histogram)

    field_stats['regional_stats'] = {'histogram': regional_frequency_pairs}
    field_stats['labels'] = labels

    return field_stats


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

        # generate the per-group statistics
        # the transpose and to_dict ensures that the output looks similar to
        # ['item']['mean'] for every item in the group
        location_stats = dataset[tag].agg({'mean': np.mean,
            'std': lambda x: np.std(x)}).replace(np.nan, 0, inplace=True).transpose().to_dict()

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
            field_stats['locations'][group_name]['percent_reported'] = percent_reported
            field_stats['locations'][group_name]['percent_missing'] = percent_missing

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


def generate_single_choice_field_stats(tag, dataset, field_options):
    '''Returns statistics (frequency histogram, number/percentage of actual
    reports, number/percentage of missing reports) for a specified form field
    tag. The associated form field takes one value of several options.


    Parameters
    - tag: a form field tag
    - dataset: a pandas DataFrame or group series with the submission data
    - field_options: an iterable (queryset or no) of form field options

    Returns
    - a dictionary (or nested dictionary, if data set is grouped) with the
    above statistics, as well as the labels for each of the options. Both the
    histogram and the labels are generated as lists, so they are ordered.'''

    options = [x.option for x in field_options]
    labels = [x.description for x in field_options]

    field_stats = {'type': 'single-choice', 'labels': labels}

    if hasattr(dataset, 'groups'):
        # the data is grouped, so per-group statistics will be generated
        group_names = dataset.groups.keys()

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
            location_stats[group_name]['percent_reported'] = percent_reported
            location_stats[group_name]['percent_missing'] = percent_missing

            histogram = make_histogram(options, temp)
            histogram_mod = lambda x: (x, percent_of(x, reported))
            histogram2 = map(histogram_mod, histogram)

            location_stats[group_name] = {'histogram': histogram2}

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
                 'percent_missing': percent_missing}

        field_stats.update(stats)

    return field_stats


def generate_mutiple_choice_field_stats(tag, dataset, field_options):
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

    options = [x.option for x in field_options]
    labels = [x.description for x in field_options]

    if hasattr(dataset, 'groups'):
        group_names = dataset.groups.keys()

        field_stats['labels'] = labels
        location_stats = {}

        for group_name in group_names:
            temp = dataset.get_group(group_name).get(tag)

            missing = sum(not x for x in temp)
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

            histogram_mod = lambda x: (x, percent_of(x, total))

            histogram2 = map(histogram_mod, histogram)

            location_stats[group_name] = {'histogram': histogram2}

        field_stats['locations'] = location_stats
    else:
        missing = sum(not x for x in dataset[tag])
        total = dataset[tag].size
        reported = total - missing
        percent_reported = percent_of(reported, total)
        percent_missing = percent_of(missing, total)

        histogram = summarize_options(options, dataset[tag])

        histogram_mod = lambda x: (x, percent_of(x, total))

        histogram2 = map(histogram_mod, histogram)

        stats = {'histogram': histogram2, 'reported': reported,
                 'missing': missing, 'percent_reported': percent_reported,
                 'percent_missing': percent_missing, 'labels': labels}

        field_stats.update(stats)

    return field_stats


def generate_process_data(form, qs, location_root=None, grouped=True, tags=None):
    '''Generates process statistics for either a location and its descendants,
    or for a sample. Optionally generates statistics for an entire region, or
    for groups of regions.


    Parameters
    - form: a Form instance
    - location_id: the pk of the location to retrieve statistics for
    - sample: a sample instance, with locations to retrieve statistics for
    - grouped: when retrieving statistics for a location, specify whether or
    not to retrieve statistics on a per-group basis.
    - tags: an iterable of tags to retrieve statistics for'''
    process_summary = {}
    if not location_root:
        location_root = Location.root()
    location_types = [ltype.name for ltype in location_root.sub_location_types()]

    try:
        data_frame, single_choice_tags, multiple_choice_tags = get_data_records(form, qs, location_root, tags)
    except Exception:
        return process_summary

    # by casting the retrieval of these models to a list, we force an early evaluation
    # saving repetitive database requests for each individual object as we iterate
    # through each item
    if tags:
        form_groups = list(FormGroup.objects.filter(pk__in=FormField.objects.filter(tag__in=tags).values_list('group__pk', flat=True)))
    else:
        form_groups = list(form.groups.all())
    form_fields = list(FormField.objects.filter(group__form=form).select_related())
    form_field_options = list(FormFieldOption.objects.filter(field__group__form=form).select_related())

    if data_frame.empty:
        return process_summary

    if not tags:
        tags = single_choice_tags + multiple_choice_tags
        tags.sort()

    if not grouped:
        process_summary['type'] = 'normal'
        sample_summary = []

        for group in form_groups:
            group_summary = []

            for form_field in filter(lambda field: field.group == group and field.tag in tags, form_fields):
                field_stats = {}

                if not filter(lambda option: option.field == form_field, form_field_options):
                    # processing a field taking a numeric value
                    field_stats = generate_numeric_field_stats(form_field.tag, data_frame)
                else:
                    # processing a choice field, but what type?
                    field_options = filter(lambda option: option.field == form_field, form_field_options)

                    if form_field.tag in single_choice_tags:
                        field_stats = generate_single_choice_field_stats(form_field.tag, data_frame, field_options)
                    else:
                        field_stats = generate_mutiple_choice_field_stats(form_field.tag, data_frame, field_options)

                group_summary.append((form_field.tag, form_field.description, field_stats))

            sample_summary.append((group.name, group_summary))

        process_summary['summary'] = sample_summary

        children = list(location_root.get_children())
        sub_locations = [(location.pk, location.name) for location in children]
    else:
        if not location_types:
            return process_summary

        location_names = []

        process_summary['type'] = 'grouped'

        for location_type in location_types:
            location_type_summary = []

            data_group = data_frame.groupby(location_type)
            location_names.extend(data_group.groups.keys())

            for group in form_groups:
                group_summary = []

                for form_field in filter(lambda field: field.group == group and field.tag in tags, form_fields):
                    field_stats = {}
                    regional_stats = {}

                    if not filter(lambda option: option.field == form_field, form_field_options):
                        field_stats = generate_numeric_field_stats(form_field.tag, data_group)

                        reported = data_frame[form_field.tag].count()
                        total = data_frame[form_field.tag].size
                        missing = total - reported
                        percent_reported = percent_of(reported, total)
                        percent_missing = percent_of(missing, total)

                        regional_stats['reported'] = reported
                        regional_stats['missing'] = missing
                        regional_stats['percent_reported'] = percent_reported
                        regional_stats['percent_missing'] = percent_missing

                        regional_stats['mean'] = data_frame[form_field.tag].mean()
                        regional_stats['std'] = np.std(data_frame[form_field.tag])
                    else:
                        field_options = filter(lambda option: option.field == form_field, form_field_options)

                        if form_field.tag in single_choice_tags:
                            field_stats = generate_single_choice_field_stats(form_field.tag, data_group, field_options)
                        else:
                            field_stats = generate_mutiple_choice_field_stats(form_field.tag, data_group, field_options)

                    if regional_stats:
                        field_stats['regional'] = regional_stats

                    group_summary.append((form_field.tag, form_field.description, field_stats))
                location_type_summary.append((group.name, group_summary))

            process_summary['detail'] = {location_type: location_type_summary}
        sub_locations = Location.objects.filter(name__in=location_names).values_list('pk', 'name')

    process_summary['sub_locations'] = sub_locations
    return process_summary
