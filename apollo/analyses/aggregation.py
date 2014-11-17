def _is_numeric(val):
    try:
        float(val)
    except TypeError:
        return False

    return True


def _percent_of(a, b):
    if not _is_numeric(a) or b == 0:
        return 0
    return float(100 * float(a) / b)


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
        child.locaton_type for child in location_root.children
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
        for locaton_type in location_types:
            kwargs = {
                'location_name_path__{}__exists'.format(locaton_type): True
            }
            subset = queryset(**kwargs)
            location_type_summary = []

            for tag in tags:
                if tag not in form.tags:
                    continue

                field = form.get_field_by_tag(tag)
                field_stats = generate_field_stats(subset, field)

                location_type_summary.append(
                    (tag, field.description, field_stats)
                )

            process_summary['groups'].append(
                (locaton_type, location_type_summary)
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
