from ..core import Service
from .models import Submission, SubmissionComment


class SubmissionsService(Service):
    __model__ = Submission


class SubmissionCommentsService(Service):
    __model__ = SubmissionComment
