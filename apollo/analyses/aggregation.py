def _numeric_field_stats(queryset, tag):
    # for numeric fields, 0 is a legal value, so some
    # jiggery is required
    token = '${}'.format(tag)
    pipeline = [
        {'$match': queryset._query},
        {'$project': {
            'status': {'$ifNull': [token, 'missing']},
            'var': token,
            '_id': 0
        }},
        # need two $project steps because 0 is a valid value, and $ifNull
        # will replace the token by its value, not the flag 'reported'
        {'$project': {
            'status': {
                '$cond': [
                    # if status is missing, keep that flag, else, replace
                    # with the 'reported' flag
                    {'$eq': ['$status', 'missing']}, 'missing', 'reported'
                ]
            },
            'var': 1,
        }},
        {'$group': {
            '_id': '$status',
            'count': {'$sum': 1},
            'mean': {'$avg': '$var'}
        }}
    ]

    collection = queryset._collection

    return collection.aggregate(pipeline)


def _single_choice_field_stats(queryset, tag):
    # for single-choice fields, 0 is not (currently) a valid
    # selection, so we don't need to do two $project
    # steps like for numeric stats
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


def _multi_choice_field_stats(queryset, tag):
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
