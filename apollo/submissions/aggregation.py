# -*- coding: utf-8 -*-
import pandas as pd

from apollo.submissions.qa.query_builder import get_logical_check_stats
from apollo.submissions.utils import make_submission_dataframe


def aggregated_dataframe(queryset, form):
    agg_locations = [anc.location_type for anc in
                     queryset.first().location.ancestors]
    # change order of locations so the largest is first
    agg_locations.reverse()
    df_submissions = make_submission_dataframe(queryset)
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
