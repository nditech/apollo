# -*- coding: utf-8 -*-
from apollo.settings import TIMEZONE
from collections import defaultdict
from datetime import datetime
from dateutil.rrule import rrule, DAILY
from logging import getLogger
from pytz import timezone

from sqlalchemy import and_, false, func, or_, not_
from sqlalchemy.orm import aliased, Load
from sqlalchemy.dialects.postgresql import array

from apollo.core import db
from apollo.locations.models import Location, LocationPath, LocationTypePath
from apollo.submissions.models import Submission

import pandas as pd

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
    conflict_group_tags = []
    if not form.untrack_data_conflicts:
        conflict_group_tags = form.get_group_tags(
            group['name'], form.CONFLICT_FIELD_TYPES)

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
    if conflict_group_tags:
        conflict_query = query.filter(
            Submission.conflicts != None,
            Submission.conflicts.has_any(array(conflict_group_tags)),
            Submission.unreachable == False)  # noqa
    else:
        conflict_query = query.filter(false())

    if group_tags:
        terms = [
            ~Submission.data.has_any(array(group_tags)),
            Submission.unreachable == False     # noqa
        ]
        if conflict_group_tags:
            terms.append(or_(
                Submission.conflicts == None,   # noqa
                ~Submission.conflicts.has_any(array(conflict_group_tags))
            ))

        missing_query = query.filter(*terms)
    else:
        missing_query = query

    if group_tags:
        terms = [Submission.data.has_all(array(group_tags))]
        if conflict_group_tags:
            terms.append(or_(
                Submission.conflicts == None,   # noqa
                ~Submission.conflicts.has_any(array(conflict_group_tags)),
            ))
        complete_query = query.filter(*terms)
    else:
        complete_query = query.filter(false())

    if group_tags:
        terms = [
            ~Submission.data.has_all(array(group_tags)),
            Submission.data.has_any(array(group_tags)),
            Submission.unreachable == False     # noqa
        ]
        if conflict_group_tags:
            terms.append(or_(
                Submission.conflicts == None,   # noqa
                ~Submission.conflicts.has_any(array(conflict_group_tags))
            ))
        partial_query = query.filter(*terms)
    else:
        partial_query = query.filter(false())

    if group_tags:
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
    else:
        offline_query = query.filter(false())

    if group_tags:
        not_opened_query = query.filter(
            and_(
                Submission.not_opened == True,  # noqa
                not_(
                    and_(
                        Submission.data.has_all(array(group_tags)),
                        Submission.not_opened == True
                    )
                )
            ))
    else:
        not_opened_query = query.filter(false())

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

    for loc_id, loc_name, count in _get_coverage_results(
            not_opened_query, depth_info.depth):
        dataset[loc_name].update({
            'Closed': count,
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
        loc_data.setdefault('Closed', 0)

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

        if group_tags:
            conflict_query = query.filter(
                Submission.conflicts != None,
                Submission.conflicts.has_any(array(group_tags)),
                Submission.unreachable == False)  # noqa
        else:
            conflict_query = query.filter(false())

        if group_tags:
            missing_query = query.filter(
                or_(
                    ~Submission.conflicts.has_any(array(group_tags)),
                    Submission.conflicts == None),
                ~Submission.data.has_any(array(group_tags)),
                Submission.unreachable == False)  # noqa
        else:
            missing_query = query

        if group_tags:
            complete_query = query.filter(
                or_(
                    Submission.conflicts == None, # noqa
                    ~Submission.conflicts.has_any(array(group_tags))),
                Submission.data.has_all(array(group_tags)))
        else:
            complete_query = query.filter(false())

        if group_tags:
            partial_query = query.filter(
                or_(
                    Submission.conflicts == None,
                    ~Submission.conflicts.has_any(array(group_tags))),
                ~Submission.data.has_all(array(group_tags)),
                Submission.data.has_any(array(group_tags)),
                Submission.unreachable == False)  # noqa
        else:
            partial_query = query.filter(false())

        if group_tags:
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
        else:
            offline_query = query.filter(false())

        if group_tags:
            not_opened_query = query.filter(
                and_(
                    Submission.not_opened == True,  # noqa
                    not_(
                        and_(
                            Submission.data.has_all(array(group_tags)),
                            Submission.not_opened == True
                        )
                    )
                ))
        else:
            not_opened_query = query.filter(false())

        data = {
            'Complete': complete_query.count(),
            'Conflict': conflict_query.count(),
            'Missing': missing_query.count(),
            'Partial': partial_query.count(),
            'Offline': offline_query.count(),
            'Closed': not_opened_query.count(),
            'name': group['name'],
            'slug': group['slug']
        }

        coverage_list.append(data)

    return coverage_list


def get_daily_progress(query, event):
    query_with_entities = query.with_entities(Submission.participant_updated)
    df = pd.read_sql(
        query_with_entities.statement,
        query_with_entities.session.bind, index_col='participant_updated',
        parse_dates=['participant_updated']).tz_localize(TIMEZONE)
    df['count'] = 1

    tz = timezone(TIMEZONE)
    start = tz.localize(datetime.combine(
        event.start.astimezone(tz), datetime.min.time()))
    end = tz.localize(
        datetime.combine(event.end.astimezone(tz), datetime.min.time()))
    df_resampled = df.loc[df.index.notnull()].append(
        pd.DataFrame({'count': 0}, index=[start])).append(
        pd.DataFrame({'count': 0}, index=[end])).resample('D').sum()

    progress = df_resampled.truncate(before=start, after=end)
    progress.loc[progress.index == start.strftime(
        '%Y-%m-%d'), 'count'] = int(
            df_resampled[df_resampled.index <= start].sum())
    progress.loc[progress.index == end.strftime(
        '%Y-%m-%d'), 'count'] = int(
            df_resampled[df_resampled.index >= end].sum())

    dp = {
        idx.date(): int(progress.loc[idx]['count'])
        for idx in progress.index
    }
    dp.update({'total': progress['count'].sum()})
    return dp


def event_days(event):
    tz = timezone(TIMEZONE)
    start = tz.localize(datetime.combine(
        event.start.astimezone(tz), datetime.min.time()))
    end = tz.localize(
        datetime.combine(event.end.astimezone(tz), datetime.min.time()))
    dates = [d.date() for d in rrule(DAILY, dtstart=start, until=end)]

    return dates


def get_stratified_daily_progress(query, event, location_type):
    response = []
    ancestor_location = aliased(Location)
    location_closure = aliased(LocationPath)

    sample_sub = query.first()
    sub_location_type = sample_sub.location.location_type

    depth_info = LocationTypePath.query.filter_by(
        ancestor_id=location_type.id,
        descendant_id=sub_location_type.id).first()

    if depth_info:
        _query = query.join(
            location_closure,
            location_closure.descendant_id == Submission.location_id).join(
                ancestor_location,
                ancestor_location.id == location_closure.ancestor_id
            ).filter(
                location_closure.depth == depth_info.depth
            ).with_entities(
                ancestor_location.name,
                ancestor_location.code,
                Submission.participant_updated
            ).options(
                Load(ancestor_location).load_only(
                    'id', 'code', 'name_translations')
            ).group_by(ancestor_location.id, Submission.participant_updated)

        df = pd.read_sql(
            _query.statement,
            _query.session.bind,
            index_col=['participant_updated'],
            parse_dates=['participant_updated']).tz_localize(TIMEZONE)
        df['count'] = 1
        tz = timezone(TIMEZONE)
        start = tz.localize(datetime.combine(
            event.start.astimezone(tz), datetime.min.time()))
        end = tz.localize(
            datetime.combine(event.end.astimezone(tz), datetime.min.time()))

        locations = Location.query.filter(
            Location.location_set == location_type.location_set,
            Location.location_type == location_type)

        for location in locations:
            if location.name not in df.loc[df.index.notnull()]['getter'].unique():  # noqa
                df = df.append(pd.DataFrame(
                    {'getter': location.name, 'count': 0, 'code': location.code},  # noqa
                    index=[start]))

        df2 = df.loc[df.index.notnull()].groupby(['getter', 'code']).resample('D').sum()  # noqa
        df2 = df2.sort_index(level='code')
        df2.index = df2.index.droplevel('code')

        for location in df2.index.get_level_values(0).unique():  # noqa
            df_resampled = df2.loc[location].append(
                pd.DataFrame({'count': 0}, index=[start])).append(
                    pd.DataFrame({'count': 0}, index=[end])).resample(
                        'D').sum()
            progress = df_resampled.truncate(before=start, after=end)
            progress.loc[progress.index == start.strftime(
                '%Y-%m-%d'), 'count'] = int(
                    df_resampled[df_resampled.index <= start].sum())
            progress.loc[progress.index == end.strftime(
                '%Y-%m-%d'), 'count'] = int(
                    df_resampled[df_resampled.index >= end].sum())
            dp = {
                idx.date(): int(progress.loc[idx]['count'])
                for idx in progress.index
            }
            dp.update({'total': progress['count'].sum()})
            response.append({'name': location, 'data': dp})

        return response
