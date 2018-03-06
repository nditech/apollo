# -*- coding: utf-8 -*-
import pandas as pd

from apollo.locations.models import Location
from apollo.submissions.models import Submission


def _extract_location_path(location_id):
    location = Location.query.get(location_id)
    return location.make_path()


def make_submission_dataframe(query, selected_tags=None, excluded_tags=None):
    query2 = query.with_entities(
        Submission.data, Submission.location_id)

    df = pd.read_sql(query2.statement, query2.session.bind)

    df_data = df['data'].apply(pd.Series)
    # remove requested tags
    if excluded_tags and isinstance(excluded_tags, list):
        df_data = df_data.drop(columns=excluded_tags)

    # restrict to requested tags
    if selected_tags and isinstance(selected_tags, list):
        df_data = df_data.filter(items=selected_tags)

    df_locations = df['location_id'].apply(
        _extract_location_path).apply(pd.Series)

    return pd.concat(
        [df_data, df_locations], axis=1, join_axes=[df_data.index])


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
