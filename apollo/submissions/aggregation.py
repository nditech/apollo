# -*- coding: utf-8 -*-
import codecs
import collections
import csv
from functools import partial
from io import StringIO
from itertools import chain

import numpy as np
import pandas as pd

from apollo.submissions.qa.query_builder import get_logical_check_stats
from apollo.submissions.utils import make_submission_dataframe


def aggregated_dataframe(queryset, form):
    agg_locations = [anc.location_type.name for anc in
                     queryset.first().location.ancestors()]
    # change order of locations so the largest is first
    agg_locations.reverse()
    df_submissions = make_submission_dataframe(queryset, form)
    all_fields = []

    # iterate through fields
    tags = form.tags
    for tag in tags:
        field = form.get_field_by_tag(tag)
        # multiselect options field
        options = field.get('options')
        if options:
            # column options are in the format tagname|option
            # e.g. (AB|1, AB|2, ...)
            # initialize the default value counts for each option
            default_options = {'{}|{}'.format(tag, option): 0
                               for option in options.values()}
            all_fields.extend(sorted(default_options.keys()))
            col = df_submissions.pop(tag).tolist()
            for i, r in enumerate(col):
                options = default_options.copy()
                # multivalued fields have a list of values
                if isinstance(r, list):
                    for o in r:
                        if o in options.values():
                            options['{}|{}'.format(tag, o)] = 1
                else:
                    if r in options.values():
                        options['{}|{}'.format(tag, r)] = 1
                col[i] = options
            df = pd.DataFrame(col)
            df_submissions = df_submissions.join(df)
        else:
            all_fields.append(tag)

    # group and aggregate
    df_agg = pd.DataFrame(columns=agg_locations + all_fields)
    for idx in range(len(agg_locations)):
        grouping = agg_locations[:idx + 1]
        for group_name, group_df in df_submissions.groupby(grouping):
            data_series = group_df.sum()[all_fields]
            if len(grouping) == 1:
                data_series[grouping[0]] = group_name
            elif len(grouping) > 1:
                for i, g in enumerate(grouping):
                    data_series[g] = group_name[i]
            df_agg = df_agg.append(data_series, ignore_index=True)

    df_agg = df_agg.fillna("")
    return df_agg


def _qa_counts(query, form):
    data = []
    if form.quality_checks:
        for check in form.quality_checks:
            d = {
                'name': check['name'],
                'description': check['description'],
                'counts': [], 'total': 0}

            results = get_logical_check_stats(query, form, check)
            for label, count in results:
                d['counts'].append({
                    'count': count,
                    'label': label
                })
                d['total'] += count

            data.append(d)

    return data


def _numeric_field_processor(column):
    return int(np.sum(column))


def _select_field_processor(options, column):
    value_counts = column.value_counts()

    return [
        value_counts.get(opt, 0) for opt in sorted(options)
    ]


def _multiselect_field_processor(options, column):
    value_counts = collections.Counter(
        chain(*(i for i in column if i is not None)))

    return [
        value_counts.get(opt, 0) for opt in sorted(options)
    ]


def aggregate_dataset(query, form, stream=False):
    data_frame = make_submission_dataframe(query, form)

    location_type_names = [
        a.location_type.name for a in query.first().location.ancestors()]

    aggregate_field_types = ['integer', 'select', 'multiselect']
    aggregate_fields = [
        fi for grp in form.data.get('groups', [])
        for fi in grp.get('fields', [])
        if fi and fi.get('type') in aggregate_field_types
    ]

    headers = ['Level'] + location_type_names
    for field in aggregate_fields:
        if field['type'] == 'integer':
            headers.append(field['tag'])
        else:
            headers.extend(
                '{tag} | {option}'.format(tag=field['tag'], option=opt)
                for opt in sorted(field['options'].values())
            )

    if stream:
        output_stream = StringIO()
        output_stream.write(codecs.BOM_UTF8.decode('utf-8'))
        writer = csv.writer(output_stream)
        writer.writerow(headers)

        yield output_stream.getvalue()
    else:
        yield headers

    for idx, level in enumerate(location_type_names):
        group_subset = location_type_names[:idx + 1]

        # the hard stuff comes here
        grouped_dataframe = data_frame.groupby(group_subset)

        # start with numeric fields. they're the easiest
        for group_key, group in grouped_dataframe:
            current_row = []

            # add level info
            current_row.append(level)

            if idx == 0:
                current_row.append(group_key)
            else:
                current_row.extend(group_key)

            # add location info
            padding_size = len(location_type_names) - len(group_subset)
            current_row.extend([''] * padding_size)

            for field in aggregate_fields:
                if field['type'] == 'integer':
                    processor = _numeric_field_processor
                    current_row.append(processor(group[field['tag']]))
                elif field['type'] == 'select':
                    processor = partial(
                        _select_field_processor, field['options'].values())
                    current_row.extend(processor(group[field['tag']]))
                else:
                    processor = partial(
                        _multiselect_field_processor,
                        field['options'].values())
                    current_row.extend(processor(group[field['tag']]))

            if stream:
                output_stream = StringIO()
                writer = csv.writer(output_stream)
                writer.writerow(current_row)

                yield output_stream.getvalue()
            else:
                yield current_row
