from __future__ import unicode_literals
from collections import OrderedDict
from logging import getLogger
from apollo.core.models import Submission

logger = getLogger(__name__)


def get_coverage(submission_queryset, group=None, location_type=None):
    if group is None and location_type is None:
        return _get_global_coverage(submission_queryset)
    else:
        return _get_group_coverage(submission_queryset, group, location_type)


def _get_group_coverage(submission_queryset, group, location_type):
    # build MongoDB aggregation pipeline
    pipeline = [
        {'$match': submission_queryset._query},
        {'$group': {
            '_id': {
                'location': '$location_name_path.{}'.format(location_type.name),
                'completion': '$completion'
            },
            'total': {'$sum': 1}
        }
        },
        {'$group': {
            '_id': {
                'location': '$_id.location',
                group: '$_id.completion.{}'.format(group)
            },
            'total': {'$sum': '$total'}
        }
        },
        {'$project': {
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
        coverage[l].update({r['completion']: r['total']})

    return coverage


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
                       for r in result if r.get('completion').get(group) == 'Complete'))
        partial = sum((r.get('total')
                      for r in result if r.get('completion').get(group) == 'Partial'))
        missing = sum((r.get('total')
                      for r in result if r.get('completion').get(group) == 'Missing'))

        coverage.update({group: {
            'Complete': complete,
            'Partial': partial,
            'Missing': missing
        }})

    return coverage
