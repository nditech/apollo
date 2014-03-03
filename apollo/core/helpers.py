from __future__ import unicode_literals
from collections import OrderedDict
from logging import getLogger
from core.documents import Location

logger = getLogger(__name__)


def get_observer_coverage(loc_qs, *groups):
    '''Given a location queryset and a list of form group names,
    returns an aggregated result of how many submissions have all
    fields entered out (Complete), how many have some of the fields
    entered out (Partial), and how many have no data entered out (Missing)
    in each specified group.

    :param: `loc_qs`: a :class: `core.documents.Location` queryset
    :param: `groups`: a list of :class: `core.documents.FormGroup` names

    :returns: an ordered dict of dictionaries, each with the structure:
        group: {
            'Complete': value,
            'Partial': value,
            'Missing': value
        }
    if no error occurs in the aggregation, else None
    '''
    # use the MongoDB aggregation framework to get each permutation
    # of groups and statuses
    pipeline = [
        {'$match': loc_qs._query},
        {'$unwind': '$submissions'},
        {'$group': {
            '_id': '$submissions.completion',
            'total': {'$sum': 1}
        }
        }]

    if groups:
        projection = {'_id': 0, 'total': '$total'}
        projection.update({group: '$_id.{}'.format(group) for group in groups})
        pipeline.append({'$project': projection})

    try:
        results = Location._collection.aggregate(
            pipeline
        )
    except Exception, e:
        print e
        logger.exception(e)
        return None

    if not results.get('ok'):
        logger.error('Aggregation did not succeed, but threw no error')
        return None

    coverage = OrderedDict()

    datasrc = results.get('result')

    # return empty set if no data
    if not datasrc:
        return coverage

    if groups:
        # groups were explicitly specified, use that
        for group in groups:
            group_complete = sum((rec['total'] for rec in datasrc if rec[group] == 'Complete'))
            group_partial = sum((rec['total'] for rec in datasrc if rec[group] == 'Partial'))
            group_missing = sum((rec['total'] for rec in datasrc if rec[group] == 'Missing'))

            coverage.update({group: {
                'Complete': group_complete,
                'Partial': group_partial,
                'Missing': group_missing
            }})
    else:
        # no groups were sent, get the group names from the data
        # WARN: No guaranteed sort order if this is used!
        groups = datasrc[0]['_id'].keys()
        for group in groups:
            group_complete = sum((rec['total'] for rec in datasrc if rec['_id'][group] == 'Complete'))
            group_partial = sum((rec['total'] for rec in datasrc if rec['_id'][group] == 'Partial'))
            group_missing = sum((rec['total'] for rec in datasrc if rec['_id'][group] == 'Missing'))

            coverage.update({group: {
                'Complete': group_complete,
                'Partial': group_partial,
                'Missing': group_missing
            }})

    return coverage
