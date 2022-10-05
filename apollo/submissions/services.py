# -*- coding: utf-8 -*-
import csv
from io import StringIO

from flask_babelex import gettext as _
from geoalchemy2.shape import to_shape

from apollo import constants
from apollo.dal.service import Service
from apollo.locations.models import LocationType
from apollo.participants.models import Sample
from apollo.submissions.models import (
    Submission, SubmissionComment, SubmissionVersion)


def export_field_value(form, submission, tag):
    field = form.get_field_by_tag(tag)
    data = submission.data.get(tag) if submission.data else None

    if field['type'] == 'multiselect':
        if data:
            try:
                return ','.join(sorted(str(i) for i in data))
            except TypeError:
                return data
    elif field['type'] == 'image':
        return data is not None

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
            participant_set_id=event.participant_set_id).all()
        tags = form.tags

        extra_field_headers = [fi.label for fi in extra_fields]

        sample_headers = [s.name for s in samples]

        if form.form_type == 'SURVEY':
            dataset_headers = [_('Serial')]
        else:
            dataset_headers = []

        dataset_headers.extend([
            _('Participant ID'), _('Name'), _('DB Phone'), _('Recent Phone')
        ] + [
            loc_type.name for loc_type in location_types
        ] + [
            _('Location'), _('Location Code'), _('Latitude'), _('Longitude')
        ] + extra_field_headers + [
            _('Registered Voters')
        ] + tags + [_('Timestamp')])

        if form.form_type == 'INCIDENT':
            dataset_headers.extend([_('Status'), _('Description')])
        else:
            dataset_headers.extend(sample_headers)
            if submission.submission_type == 'O':
                dataset_headers.append(_('Comment'))
            dataset_headers.append(_('Quarantine Status'))

        output = StringIO()
        output.write(constants.BOM_UTF8_STR)
        writer = csv.writer(output)
        writer.writerow(dataset_headers)
        yield output.getvalue()
        output.close()

        for submission in query:
            location_path = submission.location.make_path()
            if submission.submission_type == 'O':
                if submission.location.extra_data:
                    extra_data_columns = [
                        submission.location.extra_data.get(ef.name)
                        for ef in extra_fields
                    ]
                else:
                    extra_data_columns = [''] * len(extra_fields)

                record = [submission.serial_no] if form.form_type == 'SURVEY' else []   # noqa

                record.extend([
                    submission.participant.participant_id
                    if submission.participant else '',
                    submission.participant.name
                    if submission.participant else '',
                    submission.participant.primary_phone
                    if submission.participant else '',
                    submission.last_phone_number if submission.last_phone_number else '',   # noqa
                ] + [
                    location_path.get(loc_type.name, '')
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
                ])

                record += [
                    submission.updated.strftime('%Y-%m-%d %H:%M:%S')
                    if submission.updated else '',
                    submission.incident_status.value
                    if submission.incident_status else '',
                    submission.incident_description
                ] if form.form_type == 'INCIDENT' else ([
                    submission.updated.strftime('%Y-%m-%d %H:%M:%S')
                    if submission.updated else ''] + [
                        1 if sample in submission.participant.samples else 0
                        for sample in samples] + [
                                submission.comments[0].comment.replace('\n', '') # noqa
                                if submission.comments else '',
                                submission.quarantine_status.value
                                if submission.quarantine_status else '',
                            ])
            else:
                sib = submission.siblings[0]
                if submission.location.extra_data:
                    extra_data_columns = [
                        submission.location.extra_data.get(ef.name)
                        for ef in extra_fields
                    ]
                else:
                    extra_data_columns = [''] * len(extra_fields)

                record = [sib.serial_no] if form.form_type == 'SURVEY' else []

                record.extend([
                    sib.participant.participant_id
                    if sib.participant else '',
                    sib.participant.name
                    if sib.participant else '',
                    sib.participant.primary_phone
                    if sib.participant else '',
                    sib.last_phone_number if sib.last_phone_number else '',
                ] + [
                    location_path.get(loc_type.name, '')
                    for loc_type in location_types
                ] + [
                    submission.location.name,
                    submission.location.code,
                    to_shape(sib.geom).y if hasattr(sib.geom, 'desc') else '', # noqa
                    to_shape(sib.geom).x if hasattr(sib.geom, 'desc') else '', # noqa
                ] + extra_data_columns + [
                    submission.location.registered_voters
                ] + [
                    export_field_value(form, submission, tag)
                    for tag in tags])

                record += [
                    submission.updated.strftime('%Y-%m-%d %H:%M:%S')
                    if submission.updated else ''] + [
                        1 if sample in sib.participant.samples else 0
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
