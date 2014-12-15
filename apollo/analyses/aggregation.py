from itertools import izip
from operator import itemgetter


def _is_numeric(val):
    '''Safety check for trying to check if a value is numeric.'''
    try:
        float(val)
    except TypeError:
        return False

    return True


def _percent_of(a, b):
    if not _is_numeric(a) or not _is_numeric(b) or b == 0:
        return 0
    return float(100 * float(a) / b)


def _average(queryset, tag):
    '''Computes average for a particular field. Is faster than
    queryset.average() because it uses the aggregation pipeline
    instead of MapReduce like .average() does.'''
    field = queryset[0].form.get_field_by_tag(tag)
    if field.options:
        raise ValueError('Cannot compute average for non-numeric fields')

    token = '${}'.format(tag)
    pipeline = [
        {'$match': queryset._query},
        {'$group': {'_id': 'null', 'mean': {'$avg': token}}},
    ]

    collection = queryset._collection
    return collection.aggregate(pipeline).get('result')[0].get('mean')


def _numeric_field_stats(queryset, tag, location_type=None):
    # for numeric fields, 0 is a legal value, so some
    # jiggery is required
    token = '${}'.format(tag)
    data = {'type': 'numeric'}

    # build aggregation pipeline piecewise
    pipeline = [
        # mirror original query
        {'$match': queryset._query},

        # project variable
        {'$project': {'var': token}},

        # grouping
        {'$group': {
            '_id': 'null',
            'missing': {'$sum': {'$cond': [{'$eq': ['$var', 'null']}, 1, 0]}},
            'reported': {'$sum': {'$cond': [{'$ne': ['$var', 'null']}, 1, 0]}},
            'total': {'$sum': 1}
        }},

        # second stage projection - project stats
        {'$project': {
            '_id': 0,
            'location': '$_id',  # will be 'null' by default
            'missing': 1,
            'reported': 1,
            'total': 1,
            'percent_missing': {
                '$multiply': [{'$divide': ['$missing', '$total']}, 100]
            },
            'percent_reported': {
                '$multiply': [{'$divide': ['$reported', '$total']}, 100]
            }
        }}
    ]

    if location_type:
        # project the group key in the first projection
        pipeline[1]['$project']['loc_group'] = '$location_name_path.{}'.format(
            location_type)

        # allow grouping by loc_group as well
        pipeline[2]['$group']['_id'] = '$loc_group'

    collection = queryset._collection

    output = collection.aggregate(pipeline)
    results = output.get('result')

    if location_type:
        data['locations'] = {}
        for r in results:
            loc_data = {}
            loc_data.update(r)
            loc_data.pop('location')

            data['locations'][r['location']] = loc_data
    else:
        data.update(results[0])

    data['mean'] = _average(queryset, tag)

    return data


def _single_choice_field_stats(queryset, tag, location_type=None):
    # for single-choice fields, 0 is not (currently) a valid
    # selection, so we don't need to do two $project
    # steps like for numeric stats
    token = '${}'.format(tag)
    pipeline = [
        {'$match': queryset._query},
        {'$project': {
            'var': token,
            '_id': 0
        }},
        {'$group': {
            '_id': {'option': '$var', 'location': '$location'},
            'count': {'$sum': 1}
        }},
        {'$group': {
            '_id': '$_id.location',
            'histogram': {
                '$push': {'option': '$_id.option', 'count': '$count'},
            },
            'total': {'$sum': '$count'}
        }}
    ]

    if location_type:
        # add location type
        path = '$location_name_path.{}'.format(location_type)
        pipeline[1]['$project']['location'] = path

    collection = queryset._collection

    output = collection.aggregate(pipeline)
    total = queryset.count()
    form = queryset[0].form if total else None
    field = form.get_field_by_tag(tag) if form else None
    options = sorted(field.options.iteritems(),
                     key=itemgetter(1)) if field else []

    result_sort_key = lambda x: x.get('option')

    data = {
        'histogram': [],
        'labels': [i[0] for i in options],
        'missing': None,
        'reported': None,
        'percent_missing': 0,
        'percent_reported': 0,
        'total': 0,
        'type': 'single-choice'
    }

    if location_type:
        location_stats = {}
        results = output.get('result')
        for loc_data in results:
            loc_total = loc_data['total']

            missing_set = [
                i for i in loc_data['histogram'] if 'option' not in i]
            missing_data = missing_set[0] if missing_set else {'count': 0}
            loc_missing = missing_data['count']
            loc_reported = loc_total - loc_missing
            reported_set = sorted(loc_data['histogram'], key=result_sort_key)
            if missing_set:
                reported_set.remove(missing_data)

            percent_missing = _percent_of(loc_missing, loc_total)
            percent_reported = _percent_of(loc_reported, loc_total)

            histogram = [
                (i['option'], _percent_of(i['count'], loc_reported))
                for i in reported_set
            ]
            location_stats[loc_data['_id']] = {
                'missing': loc_missing,
                'reported': loc_reported,
                'total': loc_total,
                'percent_missing': percent_missing,
                'percent_reported': percent_reported,
                'histogram': histogram
            }

        data['locations'] = location_stats
    else:
        result = output.get('result')[0]
        missing_data = {'count': 0}
        missing_set = [i for i in result['histogram'] if 'option' not in i]
        if missing_set:
            missing_data = missing_set[0]

        reported_set = sorted(result['histogram'], key=result_sort_key)
        if missing_set:
            reported_set.remove(missing_data)

        data['total'] = result['total']
        data['missing'] = missing_data['count']
        data['reported'] = data['total'] - data['missing']
        data['percent_reported'] = _percent_of(data['reported'], data['total'])
        data['percent_missing'] = _percent_of(data['missing'], data['total'])
        data['histogram'] = [
            (i['option'], _percent_of(i['count'], data['reported']))
            for i in reported_set
        ]

    return data


def _multi_choice_field_stats(queryset, tag, location_type=None):
    token = '${}'.format(tag)
    pipeline = [
        {'$match': queryset._query},
        {'$project': {
            'var': token,
            '_id': 0
        }},
        {'$unwind': '$var'},
        {'$group': {
            '_id': {'option': '$var', 'location': '$location'},
            'count': {'$sum': 1}
        }},
        {'$group': {
            '_id': '$_id.location',
            'histogram': {
                '$push': {'option': '$_id.option', 'count': '$count'},
            },
        }}
    ]

    stats_pipeline = [
        {'$match': queryset._query},
        {'$project': {
            # replace all missing/nulls with empty arrays
            'var': {'$ifNull': [token, []]},
            '_id': 0
        }},
        {'$group': {
            '_id': '$location',
            'missing': {
                # count how many documents have an empty array
                '$sum': {
                    '$cond': [{'$eq': [{'$size': '$var'}, 0]}, 1, 0]
                },
            },
            'reported': {
                '$sum': {
                    '$cond': [{'$ne': [{'$size': '$var'}, 0]}, 1, 0]
                }
            }
        }},
        {'$project': {
            '_id': 0,
            'location': '$_id',
            'missing': '$missing',
            'reported': '$reported',
            'total': {'$add': ['$missing', '$reported']}
        }}
    ]

    if location_type:
        # add location type
        path = '$location_name_path.{}'.format(location_type)
        pipeline[1]['$project']['location'] = path
        stats_pipeline[1]['$project']['location'] = path

    collection = queryset._collection

    output = collection.aggregate(pipeline)
    stats_output = collection.aggregate(stats_pipeline)

    total = sum(i.get('total', 0) for i in stats_output.get('result'))
    missing = sum(i.get('missing', 0) for i in stats_output.get('result'))
    reported = total - missing

    result_sort_key = lambda x: x['option']

    form = queryset[0].form if total else None
    field = form.get_field_by_tag(tag) if form else None
    options = sorted(field.options.iteritems(),
                     key=itemgetter(1)) if field else []

    data = {
        'histogram': [],
        'labels': [i[0] for i in options],
        'missing': missing,
        'percent_missing': _percent_of(missing, total),
        'reported': reported,
        'percent_reported': _percent_of(reported, total),
        'total': total,
        'type': 'multiple-choice'
    }

    if location_type:
        location_stats = {}
        results = output.get('result')
        stats_results = stats_output.get('result')

        for loc_data, stats_data in izip(results, stats_results):
            loc_total = stats_data.get('total', 0)
            loc_reported = stats_data.get('reported', 0)
            loc_missing = stats_data.get('missing', 0)
            loc_percent_reported = _percent_of(loc_reported, loc_total)
            loc_percent_missing = _percent_of(loc_missing, loc_total)

            loc_reported_set = sorted(
                loc_data['histogram'],
                key=result_sort_key
            )

            histogram = [
                (i['option'], _percent_of(i['count'], loc_reported))
                for i in loc_reported_set
            ]

            location_stats[loc_data['_id']] = {
                'missing': loc_missing,
                'reported': loc_reported,
                'total': loc_total,
                'percent_missing': loc_percent_missing,
                'percent_reported': loc_percent_reported,
                'histogram': histogram
            }

        data['locations'] = location_stats
    else:
        result = output.get('result')[0]

        reported_set = sorted(result['histogram'], key=result_sort_key)
        data['histogram'] = [
            (i['option'], _percent_of(i['count'], data['reported']))
            for i in reported_set
        ]

    return data


def generate_field_stats(queryset, field):
    if field.options:
        if field.allows_multiple_values:
            return _multi_choice_field_stats(queryset, field.name)
        else:
            return _single_choice_field_stats(queryset, field.name)
    else:
        return _numeric_field_stats(queryset, field.name)


def generate_process_data(form, queryset, location_root, grouped=True,
                          tags=None):
    process_summary = {}
    location_types = {
        child.location_type for child in location_root.children
    }

    if not tags:
        # use all available form tags if unset
        tags = form.tags

    # return if empty queryset
    if queryset.count() == 0:
        return process_summary

    if grouped:
        if not location_types:
            return process_summary

        process_summary['type'] = 'grouped'
        process_summary['groups'] = []
        process_summary['top'] = []

        # create top level summaries
        for tag in tags:
            if tag not in form.tags:
                continue
            field = form.get_field_by_tag(tag)
            field_stats = generate_field_stats(queryset, field)

            process_summary['top'].append(
                (tag, field.description, field_stats)
            )

        # per-location level summaries
        for location_type in location_types:
            kwargs = {
                'location_name_path__{}__exists'.format(location_type): True
            }
            subset = queryset(**kwargs)
            location_type_summary = []

            for tag in tags:
                if tag not in form.tags:
                    continue

                field = form.get_field_by_tag(tag)
                if field.analysis_type != 'PROCESS':
                    # skip fields which won't feature in process analysis
                    continue

                field_stats = generate_field_stats(subset, field)

                location_type_summary.append(
                    (tag, field.description, field_stats)
                )

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
                if tag not in form.tags:
                    continue

                field = form.get_field_by_tag(tag)
                field_stats = generate_field_stats(queryset, field)
                group_summary.append(
                    (tag, field.description, field_stats)
                )

            sample_summary.append(
                (group.name, group_summary)
            )

        process_summary['summary'] = sample_summary

    return process_summary
