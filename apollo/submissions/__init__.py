from ..core import Service
from .models import Submission, SubmissionVersion, SubmissionComment


class SubmissionsService(Service):
    __model__ = Submission


class SubmissionVersionsService(Service):
    __model__ = SubmissionVersion


class SubmissionCommentsService(Service):
    __model__ = SubmissionComment
