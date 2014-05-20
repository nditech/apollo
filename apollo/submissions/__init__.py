from ..core import Service
from .models import Submission, SubmissionComment, SubmissionVersion
from ..models import LocationType
from datetime import datetime
from flask import g
from unidecode import unidecode
import csv
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO


class SubmissionsService(Service):
    __model__ = Submission

    def _set_default_filter_parameters(self, kwargs):
        """Updates the kwargs by setting the default filter parameters
        if available.

        :param kwargs: a dictionary of parameters
        """
        try:
            deployment = kwargs.get('deployment', g.get('deployment'))
            event = kwargs.get('event', g.get('event'))
            if deployment:
                kwargs.update({'deployment': deployment})
            if event:
                kwargs.update({'event': event})
        except RuntimeError:
            pass

        return kwargs

    def export_list(self, queryset, deployment):

        if queryset.count() < 1:
            yield
        else:
            submission = queryset.first()
            form = submission.form
            fields = [
                field.name for group in form.groups for field in group.fields]
            location_types = LocationType.objects(
                is_political=True, deployment=deployment)

            if submission.submission_type == 'O':
                ds_headers = [
                    'Participant ID', 'Name', 'DB Phone', 'Recent Phone'] + \
                    map(lambda location_type: location_type.name,
                        location_types)
                ds_headers += ['Location', 'PS Code', 'RV'] + fields \
                    + ['Timestamp', 'Comment']
            else:
                ds_headers = \
                    map(lambda location_type: location_type.name,
                        location_types)
                ds_headers += ['Location', 'PS Code', 'RV'] + fields \
                    + ['Timestamp']

            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(ds_headers)
            yield output.getvalue()
            output.close()

            for submission in queryset:
                if submission.submission_type == 'O':
                    record = [
                        getattr(submission.contributor, 'participant_id', ''),
                        getattr(submission.contributor, 'name', ''),
                        getattr(submission.contributor, 'phone', ''),
                        submission.contributor.phones[-1].number
                        if getattr(submission.contributor, 'phones', None) else ''] + \
                        [submission.location_name_path.get(
                         location_type.name, '')
                         for location_type in location_types] + \
                        [getattr(submission.location, 'code', '')
                         if submission.location else '',
                         getattr(submission.location, 'political_code', '')
                         if submission.location else '',
                         getattr(submission.location, 'registered_voters', '')
                         if submission.location else ''] + \
                        [getattr(submission, field, '')
                         for field in fields] + \
                        [submission.updated.strftime('%Y-%m-%d %H:%M:%S'),
                         submission.comments.first().comment
                         if submission.comments.first() else '']
                else:
                    record = [submission.location_name_path.get(
                        location_type.name, '')
                        for location_type in location_types] + \
                        [getattr(submission.location, 'code', '')
                         if submission.location else '',
                         getattr(submission.location, 'political_code', '')
                         if submission.location else '',
                         getattr(submission.location, 'registered_voters', '')
                         if submission.location else ''] + \
                        [getattr(submission, field, '')
                         for field in fields] + \
                        [submission.updated.strftime('%Y-%m-%d %H:%M:%S')]

                record = [unidecode(i) for i in record]

                output = StringIO()
                writer = csv.writer(output)
                writer.writerow(record)
                yield output.getvalue()
                output.close()


class SubmissionCommentsService(Service):
    __model__ = SubmissionComment

    def create_comment(self, submission, comment, user=None):
        return self.create(
            submission=submission, user=user, comment=comment,
            submit_date=datetime.utcnow())


class SubmissionVersionsService(Service):
    __model__ = SubmissionVersion
