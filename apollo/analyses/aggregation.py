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

    return collection.aggregate(pipeline)


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

    return collection.aggregate(pipeline)
