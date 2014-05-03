from ..core import Service
from .models import Submission, SubmissionComment, SubmissionVersion
from datetime import datetime
from flask import g


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


class SubmissionCommentsService(Service):
    __model__ = SubmissionComment

    def create_comment(self, submission, comment, user=None):
        return self.create(
            submission=submission, user=user, comment=comment,
            submit_date=datetime.utcnow())


class SubmissionVersionsService(Service):
    __model__ = SubmissionVersion
