# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd

from apollo.locations.models import Location
from apollo.submissions.models import Submission


def _extract_location_path(location_id):
    location = Location.query.get(location_id)
    return location.make_path()


def make_submission_dataframe(query, form, selected_tags=None, excluded_tags=None):
    # excluded tags have higher priority than selected tags
    fields = set(form.tags)
    if selected_tags:
        fields = fields.intersection(selected_tags)
    if excluded_tags:
        fields = fields.difference(excluded_tags)

    columns = [
        Submission.data[tag].label(tag) for tag in fields] + \
        [Submission.location_id]

    # type coercion is necessary for numeric columns
    # if we allow Pandas to infer the column type for these,
    # there's a risk that it will guess wrong, then it might
    # raise exceptions when we're calculating the mean and
    # standard deviation on those columns
    type_coercions = {
        tag: np.float64
        for tag in form.tags
        if form.get_field_by_tag(tag)['type'] == 'integer'}

    query2 = query.with_entities(*columns)

    df = pd.read_sql(query2.statement, query2.session.bind)
    df = df.astype(type_coercions)

    df_locations = df['location_id'].apply(
        _extract_location_path).apply(pd.Series)

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
