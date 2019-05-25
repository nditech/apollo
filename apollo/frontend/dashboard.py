# -*- coding: utf-8 -*-
from collections import defaultdict
from itertools import chain
from logging import getLogger

from sqlalchemy import and_, func, or_, not_
from sqlalchemy.orm import aliased, Load
from sqlalchemy.dialects.postgresql import array

from apollo.core import db
from apollo.locations.models import Location, LocationPath, LocationTypePath
from apollo.submissions.models import Submission

logger = getLogger(__name__)


def get_coverage(query, form, group=None, location_type=None):
    if group is None and location_type is None:
        return _get_global_coverage(query, form)
    else:
        return _get_group_coverage(query, form, group, location_type)


def _get_coverage_results(query, depth):
    ancestor_location = aliased(Location)
    location_closure = aliased(LocationPath)

    dataset = query.join(
        location_closure,
        location_closure.descendant_id == Submission.location_id
    ).join(
        ancestor_location,
        ancestor_location.id == location_closure.ancestor_id
    ).filter(
        location_closure.depth == depth
    ).with_entities(
        ancestor_location,
        func.count(Submission.id)
    ).options(
        Load(ancestor_location).load_only('id', 'name_translations')
    ).group_by(ancestor_location.id).all()

    return [(item[0].id, item[0].name, item[1]) for item in dataset]


def _get_group_coverage(query, form, group, location_type):
    coverage_list = []

    # check that we have data
    if not (db.session.query(query.exists()).scalar() and form and location_type):  # noqa
        return coverage_list

    group_tags = form.get_group_tags(group['name'])

    # get the location closure table depth
    sample_sub = query.first()
    sub_location_type = sample_sub.location.location_type
    try:
        depth_info = LocationTypePath.query.filter_by(
            ancestor_id=location_type.id,
            descendant_id=sub_location_type.id).one()
    except Exception:
        # TODO: replace with the proper SQLA exception classes
        return coverage_list

    # get conflict submissions first
    conflict_query = query.filter(
        Submission.conflicts != None,
        Submission.conflicts.has_any(array(group_tags)),
        Submission.unreachable != True)  # noqa

    missing_query = query.filter(
        ~Submission.data.has_any(array(group_tags)),
        or_(
            Submission.conflicts == None,
            ~Submission.conflicts.has_any(array(group_tags))),
        Submission.unreachable != True)  # noqa

    complete_query = query.filter(
        or_(
            Submission.conflicts == None,
            ~Submission.conflicts.has_any(array(group_tags))),
        Submission.data.has_all(array(group_tags)))

    partial_query = query.filter(
        or_(
            Submission.conflicts == None,
            ~Submission.conflicts.has_any(array(group_tags))),
        ~Submission.data.has_all(array(group_tags)),
        Submission.data.has_any(array(group_tags)),
        Submission.unreachable != True)  # noqa

    offline_query = query.filter(
        and_(
            Submission.unreachable == True,  # noqa
            not_(
                and_(
                    Submission.data.has_all(array(group_tags)),
                    Submission.unreachable == True
                )
            )
        ))

    dataset = defaultdict(dict)

    for loc_id, loc_name, count in _get_coverage_results(
            complete_query, depth_info.depth):
        dataset[loc_name].update({
            'Complete': count,
            'id': loc_id,
            'name': loc_name
        })

    for loc_id, loc_name, count in _get_coverage_results(
            conflict_query, depth_info.depth):
        dataset[loc_name].update({
            'Conflict': count,
            'id': loc_id,
            'name': loc_name
        })

    for loc_id, loc_name, count in _get_coverage_results(
            missing_query, depth_info.depth):
        dataset[loc_name].update({
            'Missing': count,
            'id': loc_id,
            'name': loc_name
        })

    for loc_id, loc_name, count in _get_coverage_results(
            partial_query, depth_info.depth):
        dataset[loc_name].update({
            'Partial': count,
            'id': loc_id,
            'name': loc_name
        })

    for loc_id, loc_name, count in _get_coverage_results(
            offline_query, depth_info.depth):
        dataset[loc_name].update({
            'Offline': count,
            'id': loc_id,
            'name': loc_name
        })

    for name in sorted(dataset.keys()):
        loc_data = dataset.get(name)
        loc_data.setdefault('Complete', 0)
        loc_data.setdefault('Conflict', 0)
        loc_data.setdefault('Missing', 0)
        loc_data.setdefault('Partial', 0)
        loc_data.setdefault('Offline', 0)

        coverage_list.append(loc_data)

    return coverage_list


def _get_global_coverage(query, form):
    coverage_list = []

    # check that we have data
    if not (db.session.query(query.exists()).scalar() and form):
        return coverage_list

    groups = form.data['groups']
    if not groups:
        return coverage_list

    for group in groups:
        group_tags = form.get_group_tags(group['name'])

        conflict_query = query.filter(
            Submission.conflicts != None,
            Submission.conflicts.has_any(array(group_tags)),
            Submission.unreachable != True)  # noqa

        missing_query = query.filter(
            or_(
                ~Submission.conflicts.has_any(array(group_tags)),
                Submission.conflicts == None),
            ~Submission.data.has_any(array(group_tags)),
            Submission.unreachable != True)  # noqa

        complete_query = query.filter(
            or_(
                Submission.conflicts == None,
                ~Submission.conflicts.has_any(array(group_tags))),
            Submission.data.has_all(array(group_tags)))

        partial_query = query.filter(
            or_(
                Submission.conflicts == None,
                ~Submission.conflicts.has_any(array(group_tags))),
            ~Submission.data.has_all(array(group_tags)),
            Submission.data.has_any(array(group_tags)),
            Submission.unreachable != True)  # noqa

        offline_query = query.filter(
            and_(
                Submission.unreachable == True,  # noqa
                not_(
                    and_(
                        Submission.data.has_all(array(group_tags)),
                        Submission.unreachable == True
                    )
                )
            ))

        data = {
            'Complete': complete_query.count(),
            'Conflict': conflict_query.count(),
            'Missing': missing_query.count(),
            'Partial': partial_query.count(),
            'Offline': offline_query.count(),
            'name': group['name'],
            'slug': group['slug']
        }

        coverage_list.append(data)

    return coverage_list
