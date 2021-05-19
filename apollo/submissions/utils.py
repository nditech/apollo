# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from pandas.io.json import json_normalize
from sqlalchemy import String, cast, func
from sqlalchemy.dialects.postgresql import array_agg, aggregate_order_by
from sqlalchemy.orm import aliased

from apollo.core import db
from apollo.locations.models import Location, LocationPath, LocationType
from apollo.submissions.models import Submission


def make_submission_dataframe(query, form, selected_tags=None,
                              excluded_tags=None):
    if not db.session.query(query.exists()).scalar():
        return pd.DataFrame()

    # excluded tags have higher priority than selected tags
    fields = set(form.tags)
    if selected_tags:
        fields = fields.intersection(selected_tags)
    if excluded_tags:
        fields = fields.difference(excluded_tags)

    # the 'updated' field is required for results analysis
    columns = [
        Submission.data[tag].label(tag) for tag in fields] + [
            Submission.updated
        ]

    # alias just in case the query is already joined to the tables below
    ancestor_loc = aliased(Location, name='ancestor')
    ancestor_loc_type = aliased(LocationType, name='ancestor_type')
    ancestor_loc_path = aliased(LocationPath, name='ancestor_path')
    own_loc = aliased(Location, name='own_location')

    sub_query = Submission.query.join(
        own_loc,
        Submission.location_id == own_loc.id
    ).join(
        ancestor_loc_path,
        Submission.location_id == ancestor_loc_path.descendant_id
    ).join(
        ancestor_loc,
        ancestor_loc.id == ancestor_loc_path.ancestor_id
    ).join(
        ancestor_loc_type,
        ancestor_loc.location_type_id == ancestor_loc_type.id
    ).with_entities(
        cast(ancestor_loc.name, String).label('ancestor_name'),
        cast(ancestor_loc_type.name, String).label('ancestor_type'),
        Submission.id.label('submission_id')
    ).subquery()

    # add registered voters and path extraction to the columns
    columns.append(own_loc.registered_voters.label(
        'registered_voters'))
    columns.append(
        func.json_object(
            array_agg(sub_query.c.ancestor_type),
            array_agg(sub_query.c.ancestor_name),
        ).label('location_data')
    )

    # type coercion is necessary for numeric columns
    # if we allow Pandas to infer the column type for these,
    # there's a risk that it will guess wrong, then it might
    # raise exceptions when we're calculating the mean and
    # standard deviation on those columns
    type_coercions = {
        tag: np.float64
        for tag in form.tags
        if form.get_field_by_tag(tag)['type'] == 'integer'}

    dataframe_query = query.join(
        sub_query,
        Submission.id == sub_query.c.submission_id
    ).group_by(
        Submission.id,
        own_loc.registered_voters
    ).with_entities(*columns)

    df = pd.read_sql(
        dataframe_query.statement,
        dataframe_query.session.bind
    ).astype(type_coercions)

    df_summary = pd.concat([
        df.drop('location_data', axis=1),
        json_normalize(df['location_data'])
    ], axis=1, join_axes=[df.index])

    return df_summary


def update_participant_completion_rating(submission):
    participant = submission.participant
    submissions = participant.submissions

    numerator = 0
    denominator = 0
    completion_map = {
        'Missing': 0,
        'Partial': 1,
        'Complete': 2,
        'Conflict': 2  # TODO: find a better way to compute the ratings
    }

    # TODO: fix this
    # if len(submissions) == 0:
    #     participant.completion_rating = 1
    # else:
    #     for submission in submissions:
    #         completion_values = [
    #             completion_map[i] for i in
    #             list(submission.completion.values())
    #         ]
    #         denominator += len(submission.form.groups) * 2.0
    #         numerator += sum(completion_values)

    #     try:
    #         participant.completion_rating = (numerator / denominator)
    #     except ZeroDivisionError:
    #         # this should never happen
    #         participant.completion_rating = 1
    # participant.save()
