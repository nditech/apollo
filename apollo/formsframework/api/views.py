# -*- coding: utf-8 -*-
from flask import g
from flask_apispec import MethodResource, marshal_with, use_kwargs
from webargs import fields

from apollo.api.common import BaseListResource
from apollo.api.decorators import login_or_api_key_required
from apollo.formsframework.api.schema import FormSchema
from apollo.formsframework.models import Form, events_forms


@marshal_with(FormSchema)
class FormItemResource(MethodResource):
    @login_or_api_key_required
    def get(self, form_id, **kwargs):
        deployment = getattr(g, 'deployment', None)
        if deployment:
            deployment_id = deployment.id
        else:
            deployment_id = None

        return Form.query.filter_by(
            id=form_id, deployment_id=deployment_id).one()


@use_kwargs(
    {'event_id': fields.Int(), 'form_type': fields.String()},
    locations=['query'])
class FormListResource(BaseListResource):
    schema = FormSchema()

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

        event_id = kwargs.get('event_id')
        if event_id:
            query = query.join(events_forms).filter(
                events_forms.c.event_id == event_id
            )

        return query
