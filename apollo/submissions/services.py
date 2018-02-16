# -*- coding: utf-8 -*-
from apollo.dal.service import Service
from apollo.submissions.models import (
    Submission, SubmissionComment, SubmissionVersion)


class SubmissionService(Service):
    __model__ = Submission


class SubmissionCommentService(Service):
    __model__ = SubmissionComment

    def create(self, **kwargs):
        instance = self.__model__(**kwargs)
        instance.save()


class SubmissionVersionService(Service):
    __model__ = SubmissionVersion
