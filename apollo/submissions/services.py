# -*- coding: utf-8 -*-
import csv
from geoalchemy2.shape import to_shape
from io import StringIO

from apollo import constants
from apollo.dal.service import Service
from apollo.locations.models import LocationType, Sample
from apollo.submissions.models import (
    Submission, SubmissionComment, SubmissionVersion)


def export_field_value(form, submission, tag):
    field = form.get_field_by_tag(tag)
    data = submission.data.get(tag) if submission.data else None

    if field['type'] == 'multiselect':
        if data:
            return ','.join(sorted(str(i) for i in data))

    return data


class SubmissionService(Service):
    __model__ = Submission

    def export_list(self, query):
        if query.count() == 0:
            raise StopIteration

        submission = query.first()
        event = submission.event
        form = submission.form
        extra_fields = event.location_set.extra_fields
        location_types = LocationType.query.filter_by(
            is_administrative=True,
            location_set_id=event.location_set_id).all()
        samples = Sample.query.filter_by(
            location_set_id=event.location_set_id).all()
        tags = form.tags

        extra_field_headers = [fi.label for fi in extra_fields]

        sample_headers = [s.name for s in samples]

        dataset_headers = [
            'Participant ID', 'Name', 'DB Phone', 'Recent Phone'
        ] + [
            loc_type.name for loc_type in location_types
        ] + [
            'Location', 'Location Code', 'Latitude', 'Longitude'
        ] + extra_field_headers + ['RV'] + tags + ['Timestamp']

        if form.form_type == 'INCIDENT':
            dataset_headers.extend(['Status', 'Description'])
        else:
            dataset_headers.extend(sample_headers)
            if submission.submission_type == 'O':
                dataset_headers.append('Comment')

        output = StringIO()
        output.write(constants.BOM_UTF8_STR)
        writer = csv.writer(output)
        writer.writerow(dataset_headers)
        yield output.getvalue()
        output.close()

        for submission in query:
            if submission.submission_type == 'O':
                if submission.location.extra_data:
                    extra_data_columns = [
                        submission.location.extra_data.get(ef.name)
                        for ef in extra_fields
                    ]
                else:
                    extra_data_columns = [''] * len(extra_fields)

                record = [
                    submission.participant.participant_id
                    if submission.participant else '',
                    submission.participant.name
                    if submission.participant else '',
                    submission.participant.primary_phone
                    if submission.participant else '',
                    submission.participant.phone_contacts[0].number
                    if submission.participant and
                    submission.participant.phone_contacts else '',
                ] + [
                    submission.location.make_path()[loc_type.name]
                    for loc_type in location_types
                ] + [
                    submission.location.name,
                    submission.location.code,
                    to_shape(submission.geom).y if hasattr(submission.geom, 'desc') else '',  # noqa
                    to_shape(submission.geom).x if hasattr(submission.geom, 'desc') else ''  # noqa
                ] + extra_data_columns + [
                    submission.location.registered_voters
                ] + [
                    export_field_value(form, submission, tag)
                    for tag in tags
                ]

                record += [
                    submission.updated.strftime('%Y-%m-%d %H:%M:%S')
                    if submission.updated else '',
                    submission.incident_status.value
                    if submission.incident_status else '',
                    submission.incident_description
                ] if form.form_type == 'INCIDENT' else ([
                    submission.updated.strftime('%Y-%m-%d %H:%M:%S')
                    if submission.updated else ''] + [
                        1 if sample in submission.location.samples else 0
                        for sample in samples] + [
                        submission.comments[0].comment.replace('\n', '')
                    if submission.comments else ''])
            else:
                sib = submission.siblings[0]
                if sib.location.extra_data:
                    extra_data_columns = [
                        sib.location.extra_data.get(ef.name)
                        for ef in extra_fields
                    ]
                else:
                    extra_data_columns = [''] * len(extra_fields)
                record = [
                    sib.participant.participant_id
                    if sib.participant else '',
                    sib.participant.name
                    if sib.participant else '',
                    sib.participant.primary_phone
                    if sib.participant else '',
                    sib.participant.phone_contacts[0].number
                    if sib.participant and sib.participant.phone_contacts
                    else '',
                ] + [
                    sib.location.make_path()[loc_type.name]
                    for loc_type in location_types
                ] + [
                    sib.location.name,
                    sib.location.code,
                    to_shape(sib.geom).y if hasattr(sib.geom, 'desc') else '', # noqa
                    to_shape(sib.geom).x if hasattr(sib.geom, 'desc') else '', # noqa
                ] + extra_data_columns + [
                    sib.location.registered_voters
                ] + [
                    export_field_value(form, submission, tag)
                    for tag in tags]

                record += [
                    sib.updated.strftime('%Y-%m-%d %H:%M:%S')
                    if sib.updated else ''] + [
                        1 if sample in sib.location.samples else 0
                        for sample in samples]

            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(record)
            yield output.getvalue()
            output.close()


class SubmissionCommentService(Service):
    __model__ = SubmissionComment

    def create(self, **kwargs):
        instance = self.__model__(**kwargs)
        instance.save()


class SubmissionVersionService(Service):
    __model__ = SubmissionVersion
