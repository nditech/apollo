from __future__ import unicode_literals
from collections import OrderedDict
from logging import getLogger
from ..models import Submission
from ..services import locations

logger = getLogger(__name__)


def get_coverage(submission_queryset, group=None, location_type=None):
    if group is None and location_type is None:
        return _get_global_coverage(submission_queryset)
    else:
        locs = locations.find(location_type=location_type.name)
        queryset = submission_queryset.filter_in(locs)
        return _get_group_coverage(queryset, group, location_type)


def _get_group_coverage(submission_queryset, group, location_type):
    # build MongoDB aggregation pipeline
    pipeline = [
        {'$match': submission_queryset._query},
        {
            '$group': {
                '_id': {
                    'location': '$location_name_path.{}'
                    .format(location_type.name),
                    'completion': '$completion'
                },
                'total': {'$sum': 1}
            }
        },
        {
            '$group': {
                '_id': {
                    'location': '$_id.location',
                    group: '$_id.completion.{}'.format(group)
                },
                'total': {'$sum': '$total'}
            }
        },
        {
            '$project': {
                '_id': 0,
                'location': '$_id.location',
                'completion': '$_id.{}'.format(group),
                'total': '$total'
            }
        }
    ]

    try:
        datasrc = Submission._get_collection().aggregate(pipeline)
    except Exception, e:
        logger.exception(e)
        raise e

    # reshape the result
    result = datasrc.get('result')
    if not result:
        return None

    locations = {r.get('location') for r in result}
    coverage = OrderedDict({l: {} for l in locations})
    for r in result:
        l = r.pop('location')
        coverage[l].update({r['completion']: r['total'], 'name': l})

    coverage_list = [coverage.get(l) for l in sorted(locations)] \
        if coverage else []

    return coverage_list


def _get_global_coverage(submission_queryset):
    # build the MongoDB aggregation pipeline
    pipeline = [
        {'$match': submission_queryset._query},
        {'$group': {
            '_id': '$completion',
            'total': {'$sum': 1},
        }},
        {'$project': {
            '_id': 0,
            'completion': '$_id',
            'total': '$total'
        }}
    ]

    try:
        datasrc = Submission._get_collection().aggregate(pipeline)
    except Exception as e:
        logger.exception(e)
        raise e

    result = datasrc.get('result')
    if not result:
        return None

    groups = result[0].get('completion').keys()

    # reshape the result
    coverage = OrderedDict()
    for group in groups:
        complete = sum((r.get('total')
                       for r in result
                       if r.get('completion').get(group) == 'Complete'))
        partial = sum((r.get('total')
                      for r in result
                      if r.get('completion').get(group) == 'Partial'))
        missing = sum((r.get('total')
                      for r in result
                      if r.get('completion').get(group) == 'Missing'))

        coverage.update({group: {
            'Complete': complete,
            'Partial': partial,
            'Missing': missing,
            'name': group
        }})

    # find a 'logical' sort
    submission = submission_queryset.first()
    if submission:
        group_names = [g.name for g in submission.form.groups]
    else:
        group_names = groups

    coverage_list = [coverage.get(g) for g in group_names]

    return coverage_list
