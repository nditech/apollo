# -*- coding: utf-8 -*-
from apollo.submissions.models import QUALITY_STATUSES, Submission
from flask_babel import gettext as _
from itertools import groupby
import pandas as pd

# labels
BUCKET_LABELS = {
    'OK': _('OK'),
    'FLAGGED_AND_VERIFIED': _('Verified'),
    'FLAGGED_AND_UNVERIFIED': _('Flagged'),
    'MISSING': _('Missing')
}


def aggregated_dataframe(queryset, form):
    agg_locations = [anc.location_type for anc in
                     queryset.first().location.ancestors]
    # change order of locations so the largest is first
    agg_locations.reverse()
    df_submissions = queryset.to_dataframe()
    all_fields = []

    # iterate through fields
    for group in form.groups:
        for field in group.fields:
            # multiselect options field
            if field.options:
                # column options are in the format tagname|option
                # e.g. (AB|1, AB|2, ...)
                # initialize the default value counts for each option
                default_options = {'{}|{}'.format(field.name, option): 0
                                   for option in list(field.options.values())}
                all_fields.extend(sorted(default_options.keys()))
                col = df_submissions.pop(field.name).tolist()
                for i, r in enumerate(col):
                    options = default_options.copy()
                    # multivalued fields have a list of values
                    if type(r) == list:
                        for o in r:
                            if o in list(field.options.values()):
                                options['{}|{}'.format(field.name, o)] = 1
                    else:
                        if r in list(field.options.values()):
                            options['{}|{}'.format(field.name, r)] = 1
                    col[i] = options
                df = pd.DataFrame(col)
                df_submissions = df_submissions.join(df)
            else:
                all_fields.append(field.name)

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


def _build_qa_pipeline(queryset, form):
    v_stat = ['$verification_status', Submission.VERIFICATION_STATUSES[1][0]]
    checks = []
    for qc in form.quality_checks:
        var = '$quality_checks.{}'.format(qc['name'])
        flagged_eq_step = {'$eq': [var, QUALITY_STATUSES['FLAGGED']]}
        checks.append({
            'name': {'$literal': qc['name']},
            'bucket': {
                '$cond': {
                    # if this check is OK,
                    'if': {'$eq': [var, QUALITY_STATUSES['OK']]},
                    # set bucket to 'OK'
                    'then': BUCKET_LABELS['OK'],
                    'else': {'$cond': {
                        # elif this check is flagged and verified
                        'if': {'$and': [
                            flagged_eq_step,
                            {'$eq': v_stat}
                        ]},
                        # set bucket to 'FLAGGED_AND_VERIFIED'
                        'then': BUCKET_LABELS['FLAGGED_AND_VERIFIED'],
                        'else': {'$cond': {
                            # elif the check is flagged and not verified
                            'if': {'$and': [
                                flagged_eq_step,
                                {'$ne': v_stat}
                            ]},
                            # set to 'FLAGGED_AND_UNVERIFIED'
                            'then': BUCKET_LABELS['FLAGGED_AND_UNVERIFIED'],
                            # otherwise set to 'MISSING'
                            'else': BUCKET_LABELS['MISSING']
                        }}
                    }}
                }
            }
        })
    project_stage = {
        '$project': {
            '_id': 0,
            'checks': checks
        }
    }

    pipeline = [
        {'$match': queryset._query},
        project_stage,
        {'$unwind': '$checks'},
        {'$group': {
            '_id': {'name': '$checks.name', 'bucket': '$checks.bucket'},
            'count': {'$sum': 1}
        }}
    ]

    return pipeline


def __flag_sort_key(record):
    return record.get('_id').get('name')


def __bucket_sort_key(record):
    return record.get('_id').get('bucket')


def __total_counts(bucket_data):
    return sum(i.get('count') for i in bucket_data)


def _quality_check_aggregation(queryset, form):
    pipeline = _build_qa_pipeline(queryset, form)

    collection = queryset._collection
    result = collection.aggregate(pipeline).get('result')

    qc_meta = {
        qc.get('name'): qc.get('description') for qc in form.quality_checks}
    sorted_result = sorted(result, key=__flag_sort_key)

    data = []

    # use a two-level sort/group: first by flag name
    for flag_name, flag_dataset in groupby(sorted_result, key=__flag_sort_key):
        d = {
            'name': flag_name,
            'counts': [],
            'description': qc_meta.get(flag_name)
        }

        # then by bucket name
        sorted_flag_dataset = sorted(flag_dataset, key=__bucket_sort_key)

        # i wish this dict creation was unnecessary, but we need to do
        # something even when the bucket is missing from the set in
        # BUCKET_LABELS
        flag_data_dict = {
            k: list(v)
            for k, v in groupby(sorted_flag_dataset, key=__bucket_sort_key)
        }
        for bucket_name in list(BUCKET_LABELS.values()):
            if bucket_name in flag_data_dict:
                d['counts'].append({
                    'count': __total_counts(flag_data_dict.get(bucket_name)),
                    'label': bucket_name
                })
            else:
                d['counts'].append({
                    'count': 0,
                    'label': bucket_name
                })
        data.append(d)

    return data
