# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from sqlalchemy.orm import aliased
from sqlalchemy.dialects.postgresql import array_agg, aggregate_order_by

from apollo.core import db
from apollo.locations.models import (Location, LocationPath, LocationType,
                                     LocationTypePath)
from apollo.submissions.models import Submission


def make_submission_dataframe(query, form, selected_tags=None,
                              excluded_tags=None):
    if not db.session.query(query.exists()).scalar():
        return pd.DataFrame()

    # get column headers by getting all ancestor names
    # of the submission location's location type
    sample_submission = query.first()
    location_type = sample_submission.location.location_type
    # ancestor_table = aliased(LocationType)
    # ancestor_names = LocationType.query.join(
    #     LocationTypePath, LocationType.id == LocationTypePath.descendant_id
    # ).join(
    #     ancestor_table, ancestor_table.id == LocationTypePath.ancestor_id
    # ).filter_by(id=location_type.id).with_entities(
    #     ancestor_table.name).order_by(LocationTypePath.depth).all()
    ancestor_names = [a.name for a in location_type.ancestors()] + \
        [location_type.name]

    # excluded tags have higher priority than selected tags
    fields = set(form.tags)
    if selected_tags:
        fields = fields.intersection(selected_tags)
    if excluded_tags:
        fields = fields.difference(excluded_tags)

    columns = [
        Submission.data[tag].label(tag) for tag in fields]

    # alias just in case the query is already joined to the tables below
    loc = aliased(Location)
    loc_path = aliased(LocationPath)

    # add path extraction to the columns
    columns.append(
        array_agg(aggregate_order_by(loc.name, loc_path.depth.desc())).label(
            'location_data'))

    query2 = query.join(
        loc_path, Submission.location_id == loc_path.descendant_id
    ).join(loc, loc.id == loc_path.ancestor_id)

    # type coercion is necessary for numeric columns
    # if we allow Pandas to infer the column type for these,
    # there's a risk that it will guess wrong, then it might
    # raise exceptions when we're calculating the mean and
    # standard deviation on those columns
    type_coercions = {
        tag: np.float64
        for tag in form.tags
        if form.get_field_by_tag(tag)['type'] == 'integer'}

    dataframe_query = query2.with_entities(*columns).group_by(Submission.id)

    df = pd.read_sql(dataframe_query.statement, dataframe_query.session.bind)
    df = df.astype(type_coercions)

    df_locations = df['location_data'].apply(pd.Series).rename(
        columns=dict(enumerate(ancestor_names)))

    return pd.concat(
        [df, df_locations], axis=1, join_axes=[df.index])


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
