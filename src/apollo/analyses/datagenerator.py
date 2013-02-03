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


def get_data_records(form, location_root=0):
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


def numeric_process_data(tag, group):
    field_data = {}

    regions = group[tag].aggregate({'mean': np.mean,
        'std': lambda x: np.std(x)})

    # tag field as a numeric field
    field_data['type'] = 'numeric'
    field_data['regions'] = regions.transpose().to_dict()

    group_names = group.groups.keys()

    for group_name in group_names:
        temp = group[tag].get_group(group_name)
        reported = temp.count()
        missing = temp.size - reported
        field_data['regions'][group_name]['reported'] = reported
        field_data['regions'][group_name]['missing'] = missing

    return field_data


def univariate_process_data(tag, group, field_options):
    field_data = {}
    #    field__group__form=form))
    values = [x.option for x in field_options]
    descriptions = [x.description for x in field_options]

    regions = {}

    group_names = group.groups.keys()

    for group_name in group_names:
        temp = group.get_group(group_name).get(tag)
        histogram = make_histogram(values, temp)

        regions[group_name] = {'stats': histogram}
        reported = temp.count()
        regions[group_name]['reported'] = reported
        regions[group_name]['missing'] = temp.size - reported

    field_data['regions'] = regions
    field_data['type'] = 'single-choice'
    field_data['legend'] = descriptions

    return field_data


def multivariate_process_data(tag, group, field_options):
    field_data = {'type': 'multiple-choice'}

    values = [x.option for x in field_options]
    descriptions = [x.description for x in field_options]

    regions = {}

    for name, series in group[tag]:
        # TODO: this might be needed for the (almost certain) refactor
        # num_points = len(series)
        summary = summarize_options(values, series)

        mapping = []

        for index, value in enumerate(values):
            mapping.append(summary[index])

            regions[name] = {'stats': mapping}

        temp = group[tag].get_group(name)
        missing = sum(not x for x in temp)
        regions[name]['missing'] = missing
        regions[name]['total'] = temp.size
        regions[name]['reported'] = temp.size - missing

    field_data['regions'] = regions
    field_data['legend'] = descriptions

    return field_data


def filter_tags(form, univariate_tags, multivariate_tags):
    fields = FormField.objects.filter(group__form=form)

    univariate_process_tags = [field.tag for field in fields if not field.voteoption_set.all() and field.tag in univariate_tags]
    multivariate_process_tags = [field.tag for field in fields if not field.voteoption_set.all() and field.tag in multivariate_tags]

    univariate_result_tags = [x for x in univariate_tags if x not in univariate_process_tags]
    multivariate_result_tags = [x for x in multivariate_tags if x not in multivariate_process_tags]

    return (univariate_process_tags, multivariate_process_tags, univariate_result_tags, multivariate_result_tags)


def generate_process_data(form, location_id=0):
    process_summary = {}

    location_types = sub_location_types(location_id)

    if not location_types:
        return process_summary

    data_frame, single_choice_tags, multichoice_tags = get_data_records(form, location_id)

    single_process_tags, multichoice_process_tags, single_result_tags, multichoice_result_tags = filter_tags(form,
        single_choice_tags, multichoice_tags)

    form_groups = form.groups.all()

    for location_type in location_types:
        location_type_summary = {}

        data_group = data_frame.groupby(location_type)

        for group in form_groups:
            group_summary = []
            for form_field in group.fields.all():
                field_summary = {}
                global_summary = {}

                if not form_field.options.count():
                    # process numeric field
                    field_summary = numeric_process_data(form_field.tag, data_group)

                    global_mean = np.mean(data_frame[form_field.tag])
                    global_std = np.std(data_frame[form_field.tag])

                    global_summary = {'mean': global_mean, 'std': global_std}

                else:
                    field_options = form_field.options.all()

                    if form_field.tag in single_process_tags:
                        field_summary = univariate_process_data(form_field.tag,
                                                                data_group,
                                                                field_options)
                    else:
                        field_summary = multivariate_process_data(form_field.tag,
                                                                  data_group,
                                                                  field_options)

                if global_summary:
                    field_summary['global'] = global_summary

                group_summary.append((form_field.tag, form_field.description, field_summary))

            location_type_summary[group.name] = group_summary
        process_summary[location_type] = location_type_summary

    return process_summary


def generate_results_data(location_root, form):
    pass
