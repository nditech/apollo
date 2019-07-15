# -*- coding: utf-8 -*-
from flask import g
from flask_apispec import MethodResource, marshal_with, use_kwargs
from webargs import fields

from apollo.api.common import BaseListResource
from apollo.api.decorators import login_or_api_key_required
from apollo.submissions.api.schema import SubmissionSchema
from apollo.submissions.models import Submission


@marshal_with(SubmissionSchema)
@use_kwargs({'event_id': fields.Int()}, locations=['query'])
class SubmissionItemResource(MethodResource):
    @login_or_api_key_required
    def get(self, submission_id, **kwargs):
        deployment = getattr(g, 'deployment', None)

        event_id = kwargs.get('event_id')
        if event_id is None:
            event = getattr(g, 'event', None)
            event_id = event.id if event else None

        deployment_id = deployment.id if deployment else None

        submission = Submission.query.filter_by(
            deployment_id=deployment_id, event_id=event_id,
            id=submission_id
        ).first_or_404()

        return submission


@use_kwargs({'event_id': fields.Int(), 'form_id': fields.Int(required=True),
            'submission_type': fields.Str()}, locations=['query'])
class SubmissionListResource(BaseListResource):
    schema = SubmissionSchema()

    def get_items(self, **kwargs):
        deployment = getattr(g, 'deployment', None)
        deployment_id = deployment.id if deployment else None

        form_id = kwargs.get('form_id')

        event_id = kwargs.get('event_id')
        if not event_id:
            event = getattr(g, 'event', None)
            event_id = event.id if event else None

        query = Submission.query.filter_by(
            deployment_id=deployment_id,
            event_id=event_id,
            form_id=form_id
        )

        submission_type = kwargs.get('submission_type')
        if submission_type:
            query = query.filter_by(submission_type=submission_type)

        return query
