# -*- coding: utf-8 -*-
from flask import g
from flask_apispec import MethodResource, marshal_with, use_kwargs
from sqlalchemy import or_
from webargs import fields

from apollo.api.common import BaseListResource
from apollo.api.decorators import protect
from apollo.formsframework.api.schema import FormSchema
from apollo.formsframework.models import Form, events_forms


@marshal_with(FormSchema)
class FormItemResource(MethodResource):
    @protect
    def get(self, form_id, **kwargs):
        deployment = getattr(g, 'deployment', None)
        if deployment:
            deployment_id = deployment.id
        else:
            deployment_id = None

        return Form.query.filter_by(
            id=form_id, deployment_id=deployment_id).first_or_404()


@use_kwargs(
    {'events': fields.DelimitedList(fields.Int()),
     'form_type': fields.String(),
     'last_modified_after': fields.DateTime()},
    locations=['query'])
class FormListResource(BaseListResource):
    schema = FormSchema()

    @protect
    def get_items(self, **kwargs):
        deployment = getattr(g, 'deployment', None)
        if deployment:
            deployment_id = deployment.id
        else:
            deployment_id = None

        query = Form.query.filter_by(deployment_id=deployment_id)

        form_type = kwargs.get('form_type')
        if form_type:
            query = query.filter_by(
                form_type=form_type, deployment_id=deployment_id)

        event_ids = kwargs.get('events')
        if event_ids:
            term = or_(*[
                events_forms.c.event_id == event_id
                for event_id in event_ids
            ])
            query = query.join(events_forms).filter(term)

        last_modified = kwargs.get('last_modified_after')
        if last_modified:
            last_modified_str = last_modified.strftime('%Y%m%d%H%M%S%f')
            query = query.filter(Form.version_identifier > last_modified_str)

        return query
