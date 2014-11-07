def generate_numeric_field_stats(queryset, tag):
    token = '${}'.format(tag)
    pipeline = [
        {'$match': queryset._query},
        {'$project': {
            'status': {'$cond': [token, 'reported', 'missing']},
            'var': token,
            '_id': 0
        }},
        {'$group': {
            '_id': '$status',
            'count': {'$sum': 1},
            'mean': {'$avg': '$var'}
        }}
    ]

    collection = queryset._collection

    result = collection.aggregate(pipeline).get('result')
    data = {
        'type': 'numeric',
        'missing': 0,
        'reported': 0,
        'mean': 0,
        'percent_missing': 0,
        'percent_reported': 0
    }

    for r in result:
        if r['_id'] == 'missing':
            data['missing'] = r['count']
            data['percent_missing'] = float(r['count']) / queryset.count()
        if r['_id'] == 'reported':
            data['reported'] = r['count']
            data['mean'] = r['mean']
            data['percent_reported'] = float(r['count']) / queryset.count()

    return data


def generate_single_choice_field_stats(queryset, tag):
    token = '${}'.format(tag)
    pipeline = [
        {'$match': queryset._query},
        {'$project': {
            'status': {'$cond': [token, 'reported', 'missing']},
            'var': token,
            '_id': 0
        }},
        {'$group': {
            '_id': {'status': '$status', 'option': '$var'},
            'count': {'$sum': 1}
        }}
    ]

    collection = queryset._collection

    result = collection.aggregate(pipeline).get('result')
    form = queryset[0].form
    field = form.get_field_by_tag(tag)
    data = {
        'labels': field.options.keys(),  # need to change this so it's sorted
        'missing': 0,
        'reported': 0,
        'total': queryset.count(),
        'percent_missing': 0,
        'percent_reported': 0,
        'type': 'single-choice'
    }

    

    return data


def generate_multi_choice_field_stats(queryset, tag):
    token = '${}'.format(tag)
    pipeline = [
        {'$match': queryset._query},
        {'$project': {
            'var': token
        }},
        {'$unwind': '$var'},
        {'$group': {
            '_id': '$var',
            'count': {'$sum': 1}
        }}
    ]

    collection = queryset._collection

    return collection.aggregate(pipeline)
