from ..core import Service
from .models import Submission, SubmissionComment, SubmissionVersion


class SubmissionsService(Service):
    __model__ = Submission


class SubmissionCommentsService(Service):
    __model__ = SubmissionComment


class SubmissionVersionsService(Service):
    __model__ = SubmissionVersion
