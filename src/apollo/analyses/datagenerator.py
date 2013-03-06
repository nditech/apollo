from collections import Counter
import numpy as np
import pandas as pd
from core.models import *
from django.conf import settings


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
        _all = FormField.objects.filter(group__form=form).order_by('tag').values('tag', 'allow_multiple')
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

    return pd.DataFrame(submissions)


def percent_of(a, b):
    '''Returns the percentage of b that is a'''
    if np.isnan(a) or b == 0:
        return 0
    return (100 * float(a) / b)


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


def generate_single_choice_field_stats(tag, dataset, options, labels=None):
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

            histogram_mod = lambda x: (x, percent_of(x, reported))

            histogram2 = map(histogram_mod, histogram)

            location_stats[group_name]['histogram'] = histogram2

        field_stats['locations'] = location_stats
    else:
        missing = sum(not x for x in dataset[tag])
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


def generate_incident_field_stats(tag, dataset, options, labels=None, all_tags=None):
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

    field_stats = {'type': 'incidents', 'labels': labels}

    if hasattr(dataset, 'groups'):
        # the data is grouped, so per-group statistics will be generated
        group_names = dataset.groups.keys()
        group_names.sort()

        location_stats = {}

        for group_name in group_names:
            reported = dataset.get_group(group_name).get(tag).count()
            total = sum([dataset.get_group(group_name).get(field_tag).count() for field_tag in all_tags])
            missing = total - reported
            percent_reported = float(reported) / float(total) * 100.0
            percent_missing = float(missing) / float(total) * 100.0

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
        total = sum([dataset[field_tag].count() for field_tag in all_tags])
        missing = total - reported
        percent_reported = float(reported) / float(total) * 100.0
        percent_missing = float(missing) / float(total) * 100.0

        stats = {'reported': reported,
                 'missing': missing, 'percent_reported': percent_reported,
                 'percent_missing': percent_missing,
                 'total': total}

        field_stats.update(stats)

    return field_stats


def generate_field_stats(field, dataset):
    ''' In order to simplify the choice on what analysis to perform
    this method will check a few conditions and return the appropriate
    analysis for the field'''
    options = field.options.all().values_list('option', flat=True)
    labels = field.options.all().values_list('description', flat=True)

    if options:
        if field.allow_multiple:
            return generate_mutiple_choice_field_stats(field.tag, dataset, options=options, labels=labels)
        else:
            return generate_single_choice_field_stats(field.tag, dataset, options=options, labels=labels)
    else:
        return generate_numeric_field_stats(field.tag, dataset)


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
        data_frame = get_data_records(form, qs, location_root, tags)
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

    if data_frame.empty:
        return process_summary

    if not tags:
        tags = [field.tag for field in form_fields]
        tags.sort()

    if not grouped:
        process_summary['type'] = 'normal'
        sample_summary = []

        for group in form_groups:
            group_summary = []

            for form_field in filter(lambda field: field.group == group and field.tag in tags, form_fields):
                field_stats = generate_field_stats(form_field, data_frame)

                group_summary.append((form_field.tag, form_field.description, field_stats))

            sample_summary.append((group.name, group_summary))

        process_summary['summary'] = sample_summary
    else:
        if not location_types:
            return process_summary

        process_summary['type'] = 'grouped'
        process_summary['groups'] = []
        process_summary['top'] = []

        # top level summaries
        for form_field in filter(lambda field: field.tag in tags, form_fields):
            field_stats = generate_field_stats(form_field, data_frame)

            process_summary['top'].append((form_field.tag, form_field.description, field_stats))

        for location_type in location_types:
            location_type_summary = []

            data_group = data_frame.groupby(location_type)

            for form_field in filter(lambda field: field.tag in tags, form_fields):
                field_stats = generate_field_stats(form_field, data_group)

                location_type_summary.append((form_field.tag, form_field.description, field_stats))

            process_summary['groups'].append((location_type, location_type_summary))

    return process_summary


def generate_incidents_data(form, qs, location_root=None, grouped=True, tags=None):
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
    incidents_summary = {}

    if not location_root:
        location_root = Location.root()

    location_types = [ltype.name for ltype in location_root.sub_location_types()]

    try:
        data_frame = get_data_records(form, qs, location_root, tags)
    except Exception:
        return incidents_summary

    # by casting the retrieval of these models to a list, we force an early evaluation
    # saving repetitive database requests for each individual object as we iterate
    # through each item
    if tags:
        form_groups = list(FormGroup.objects.filter(pk__in=FormField.objects.filter(tag__in=tags).values_list('group__pk', flat=True)))
    else:
        form_groups = list(form.groups.all())
    form_fields = list(FormField.objects.filter(group__form=form).order_by('tag').select_related())

    if data_frame.empty:
        return incidents_summary

    if not tags:
        tags = [field.tag for field in form_fields]
    tags.sort()

    if not grouped:
        incidents_summary['type'] = 'normal'
        sample_summary = []

        for group in form_groups:
            group_summary = []

            for form_field in filter(lambda field: field.group == group and field.tag in tags, form_fields):
                field_stats = generate_incident_field_stats(form_field.tag, data_frame, ['1'], all_tags=tags)

                group_summary.append((form_field.tag, form_field.description, field_stats))

            sample_summary.append((group.name, group_summary))

        incidents_summary['summary'] = sample_summary
    else:
        if not location_types:
            return incidents_summary

        incidents_summary['type'] = 'grouped'
        incidents_summary['groups'] = []
        incidents_summary['locations'] = set()
        incidents_summary['top'] = []
        incidents_summary['tags'] = tags

        # top level summaries
        for form_field in filter(lambda field: field.tag in tags, form_fields):
            field_stats = generate_incident_field_stats(form_field.tag, data_frame, ['1'], all_tags=tags)

            incidents_summary['top'].append((form_field.tag, form_field.description, field_stats))

        for location_type in location_types:

            data_group = data_frame.groupby(location_type)
            location_stats = {}

            for form_field in filter(lambda field: field.tag in tags, form_fields):
                field_stats = generate_incident_field_stats(form_field.tag, data_group, ['1'], all_tags=tags)

                incidents_summary['locations'] = set(field_stats['locations'].keys())

                for location in field_stats['locations'].keys():
                    if not location in location_stats:
                        location_stats[location] = {}
                    location_stats[location].update({form_field.tag: (form_field.description, field_stats['locations'][location])})

            group_location_stats = [(location, location_stats[location]) for location in location_stats.keys()]
            incidents_summary['groups'].append((location_type, group_location_stats))

    return incidents_summary


def get_convergence_points(qs, tags):
    '''Generates a set of points for a convergence graph from a queryset
    and a set of tags.

    Parameters
    - qs: a Submission queryset
    - tags: the tags needed for the convergence points

    Returns
    - a dictionary with the structure:
    {
        tag1: <list of points>,
        tag2: <list of points>,
        # ...,
        tagn: <list of points>,
        updated: <list of timestamps>
    }
    '''
    submissions = list(qs.order_by('updated').data(tags).values(*(['updated'] + tags)))

    for submission in submissions:
        for tag in tags:
            if submission[tag]:
                submission[tag] = float(submission[tag])

    data_frame = pd.DataFrame(submissions).fillna(0)

    # get the cumulative sum of each column, then
    # sum across the rows to get the divisor
    summed_columns = data_frame[tags].cumsum()
    divisor = summed_columns.sum(axis=1)

    convergence_points = {}

    for tag in tags:
        dividend = summed_columns[tag] / divisor

        convergence_points.update({tag: dividend.tolist()})

    convergence_points.update({'updated': data_frame['updated'].tolist()})

    return convergence_points


def generate_rejected_ballot_stats(form, queryset, location_root=None,
                                   location_types=None, group_results=True):
    '''Generates rejected ballot statistics.

    Parameters
    - form: a checklist form
    - queryset: a queryset of submissions
    - location_root: a location to retrieve submissions under. defaults to
      the root location
    - location_types: location types used for grouping the data. defaults to
      the location types which are children of the location_root's type
    - group_results: a flag whether or not to group results. if results are not
      grouped, only the top-level statistics are generated

    Returns
    Assuming a base set of statistics as a dictionary, D, of the form:
    {reported: (number of reports, 100 * number of reports / number of locations of interest),
    missing: (number of non-reports, 100 * number of non-reports / number of locations of interest),
    rejected: (number of rejected ballots, 100 * number of rejected ballots / number of used ballots in locations of interest)}

    The output is such that
    {regional_stats: D for location_root as a whole,
    group_stats: list of {location_type: [{location: D} for each location of the location_type under the location_root]}}
    '''
    if not location_root:
        location_root = Location.root()

    if not location_types and group_results:
        location_types = [lt.name for lt in location_root.sub_location_types()]

    tags = [settings.RESULTS_QUESTIONS[key] for key in settings.RESULTS_QUESTIONS if 'ballots' in key]
    rejected_ballots_tag = settings.RESULTS_QUESTIONS['ballots_rejected']
    used_ballots_tag = settings.RESULTS_QUESTIONS['ballots_used']

    ballot_stats = {'regional_stats': {}, 'group_stats': []}

    # calculate regional stats
    data_frame = get_data_records(form, queryset, location_root, tags)

    if data_frame.empty:
        return ballot_stats

    submission_count = data_frame[rejected_ballots_tag].size
    reported_submission_count = data_frame[rejected_ballots_tag].count()
    missing_submission_count = submission_count - reported_submission_count

    percent_reported = percent_of(reported_submission_count, submission_count)
    percent_missing = 100 - percent_reported

    rejected_ballots_count = data_frame[rejected_ballots_tag].sum()
    used_ballots_count = data_frame[used_ballots_tag].sum()

    percent_rejected = percent_of(rejected_ballots_count, used_ballots_count)

    ballot_stats['regional_stats'].update({'reported': (reported_submission_count, percent_reported),
        'missing': (missing_submission_count, percent_missing),
        'rejected': (rejected_ballots_count, percent_rejected)})

    if group_results:
        for location_type in location_types:
            if location_type not in data_frame:
                continue

            data_group = data_frame.groupby(location_type)

            group_stats = []

            names = data_group.groups.keys()

            for name in names:
                local_submission_count = data_group.get_group(name).get(rejected_ballots_tag).size
                local_report_count = data_group.get_group(name).get(rejected_ballots_tag).count()
                local_missing_count = local_submission_count - local_report_count

                local_report_percentage = percent_of(local_report_count, local_submission_count)
                local_missing_percentage = 100 - local_report_percentage

                local_rejection_count = data_group.get_group(name).get(rejected_ballots_tag).sum()
                local_usage_count = data_group.get_group(name).get(used_ballots_tag).sum()

                local_rejection_percentage = percent_of(local_rejection_count, local_usage_count)

                group_stats.append({name: {'reported': (local_report_count, local_report_percentage),
                    'missing': (local_missing_count, local_missing_percentage),
                    'rejected': (local_rejection_count, local_rejection_percentage)}})

            ballot_stats['group_stats'].append({location_type: group_stats})

    return ballot_stats
