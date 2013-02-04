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


def get_data_records(form, location_root=0, sample=None):
    '''
    Given a form model instance and a location pk, generate a pandas DataFrame
    containing the submitted form values for locations below the specified
    location_root.
    '''
    # fields that can store multiple variables are to be handled differently
    multivariate_fields = FormField.objects.filter(group__form=form, allow_multiple=True).values_list('tag', flat=True)
    regular_fields = FormField.objects.filter(group__form=form, allow_multiple=False).values_list('tag', flat=True)
    all_fields = list(multivariate_fields) + list(regular_fields)

    # retrieve normal and reversed locations graphs
    if not sample:
        locations_graph = get_locations_graph()
        locations_graph_reversed = get_locations_graph(reverse=True)
        location_types = sub_location_types(location_root)

        # if the location_root is defined, then we'll retrieve all sublocations based
        # on the location_root which will be used for retrieving submissions if not
        # we'll just use all locations in the graph
        if location_root:
            sub_location_ids = nx.dfs_tree(locations_graph_reversed, location_root).nodes()
        else:
            sub_location_ids = locations_graph.nodes()
    else:
        # TODO: adjust this so it works even if the location has descendants
        location_types = None
        sub_location_ids = sample.locations.all().values_list('pk')

    # in addition to retrieving field data, also retrieve the location_id
    submissions = list(Submission.objects.filter(location__pk__in=sub_location_ids, observer=None).data(all_fields).values(*(['location_id'] + all_fields)))

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
    return (100 * float(a) / b)


def generate_numeric_field_summary(tag, dataset):
    field_summary = {'type': 'numeric'}

    if hasattr(dataset, 'groups'):
        group_names = dataset.groups.keys()

        location_stats = dataset[tag].agg({'mean': np.mean,
            'std': lambda x: np.std(x)}).transpose().to_dict()

        field_summary['locations'] = location_stats

        for group_name in group_names:
            temp = dataset[tag].get_group(group_name)
            total = temp.size
            reported = temp.count()
            missing = total - reported
            percent_reported = percent_of(reported, total)
            percent_missing = percent_of(missing, total)

            field_summary['locations'][group_name]['reported'] = reported
            field_summary['locations'][group_name]['missing'] = missing
            field_summary['locations'][group_name]['percent_reported'] = percent_reported
            field_summary['locations'][group_name]['percent_missing'] = percent_missing

    else:
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

        field_summary.update(stats)

    return field_summary


def generate_single_choice_field_summary(tag, dataset, field_options):
    field_summary = {'type': 'single-choice'}

    options = [x.option for x in field_options]
    labels = [x.description for x in field_options]

    if hasattr(dataset, 'groups'):
        group_names = dataset.groups.keys()

        location_stats = {'labels': labels}

        for group_name in group_names:
            temp = dataset.get_group(group_name).get(tag)
            histogram = make_histogram(options, temp)

            location_stats[group_name] = {'histogram': histogram}
            reported = temp.count()
            total = temp.size
            missing = total - reported
            percent_reported = percent_of(reported, total)
            percent_missing = percent_of(missing, total)
            location_stats[group_name]['missing'] = missing
            location_stats[group_name]['reported'] = reported
            location_stats[group_name]['percent_reported'] = percent_reported
            location_stats[group_name]['percent_missing'] = percent_missing

        field_summary['locations'] = location_stats
    else:
        histogram = make_histogram(options, dataset[tag])

        reported = dataset[tag].count()
        total = dataset[tag].size
        missing = total - reported
        percent_reported = percent_of(reported, total)
        percent_missing = percent_of(missing, total)

        stats = {'histogram': histogram, 'reported': reported,
                 'missing': missing, 'percent_reported': percent_reported,
                 'percent_missing': percent_missing, 'labels': labels}

        field_summary.update(stats)

    return field_summary


def generate_mutiple_choice_field_summary(tag, dataset, field_options):
    field_summary = {'type': 'multiple-choice'}

    options = [x.option for x in field_options]
    labels = [x.description for x in field_options]

    if hasattr(dataset, 'groups'):
        group_names = dataset.groups.keys()

        location_stats = {'labels': labels}

        for group_name in group_names:
            temp = dataset.get_group(group_name).get(tag)
            histogram = summarize_options(options, temp)

            location_stats[group_name] = {'histogram': histogram}

            missing = sum(not x for x in temp)
            reported = temp.size - missing
            total = temp.size
            percent_missing = percent_of(missing, total)
            percent_reported = percent_of(reported, total)
            location_stats[group_name]['missing'] = missing
            location_stats[group_name]['reported'] = reported
            location_stats[group_name]['percent_reported'] = percent_reported
            location_stats[group_name]['percent_missing'] = percent_missing

        field_summary['locations'] = location_stats
    else:
        histogram = summarize_options(options, dataset[tag])

        missing = sum(not x for x in dataset[tag])
        total = dataset[tag].size
        reported = total - missing
        percent_reported = percent_of(reported, total)
        percent_missing = percent_of(missing, total)

        stats = {'histogram': histogram, 'reported': reported,
                 'missing': missing, 'percent_reported': percent_reported,
                 'percent_missing': percent_missing, 'labels': labels}

        field_summary.update(stats)

    return field_summary


def generate_process_data(form, location_id=0, sample=None, grouped=True):
    '''This assumes nobody will call this with both a valid location_id and sample'''
    process_summary = {}

    data_frame, single_choice_tags, multiple_choice_tags = get_data_records(form, location_id, sample)

    form_groups = form.groups.all()

    if sample or not grouped:
        process_summary['type'] = 'sample'
        sample_summary = []

        for group in form_groups:
            group_summary = []

            for form_field in group.fields.all():
                field_summary = {}

                if not form_field.options.count():
                    # processing a field taking a numeric value
                    field_summary = generate_numeric_field_summary(form_field.tag, data_frame)
                else:
                    # processing a choice field, but what type?
                    field_options = form_field.options.all()

                    if form_field.tag in single_choice_tags:
                        field_summary = generate_single_choice_field_summary(form_field.tag, data_frame, field_options)
                    else:
                        field_summary = generate_mutiple_choice_field_summary(form_field.tag, data_frame, field_options)

                group_summary.append((form_field.tag, form_field.description, field_summary))

            sample_summary.append((group.name, group_summary))

        process_summary['summary'] = sample_summary
    else:
        location_types = sub_location_types(location_id)

        if not location_types:
            return process_summary

        for location_type in location_types:
            location_type_summary = []

            data_group = data_frame.groupby(location_type)

            for group in form.groups.all():
                group_summary = []

                for form_field in group.fields.all():
                    field_summary = {}
                    regional_stats = {}

                    if not form_field.options.count():
                        field_summary = generate_numeric_field_summary(form_field.tag, data_group)

                        regional_stats['mean'] = data_frame[form_field.tag].mean()
                        regional_stats['std'] = np.std(data_frame[form_field.tag])
                    else:
                        field_options = form_field.options.all()

                        if form_field.tag in single_choice_tags:
                            field_summary = generate_single_choice_field_summary(form_field.tag, data_group, field_options)
                        else:
                            field_summary = generate_mutiple_choice_field_summary(form_field.tag, data_group, field_options)

                    if regional_stats:
                        field_summary['regional'] = regional_stats

                    group_summary.append((form_field.tag, form_field.description, field_summary))

                location_type_summary.append((group.name, group_summary))

            process_summary[location_type] = location_type_summary

    return process_summary
