# -*- coding: utf-8 -*-
from flask import g
from flask_apispec import MethodResource, marshal_with, use_kwargs
from sqlalchemy import false
from webargs import fields

from apollo.api.common import BaseListResource
from apollo.deployments.api.schema import EventSchema
from apollo.deployments.models import Event

EVENT_LIST_QUERY_MAP = {
    # the timestamp to start filtering events from as an ISO 8601 format string
    'from': fields.DateTime(),
    # the timestamp to stop filtering events to as an ISO 8601 format string
    'to': fields.DateTime(),
}


class EventItemResource(MethodResource):
    @marshal_with(EventSchema)
    def get(self, event_id):
        deployment = getattr(g, 'deployment', None)
        if deployment:
            deployment_id = deployment.id
        else:
            deployment_id = None

        return Event.query.filter_by(
            id=event_id, deployment_id=deployment_id).first_or_404()


@use_kwargs(EVENT_LIST_QUERY_MAP, locations=['query'])
class EventListResource(BaseListResource):
    schema = EventSchema()

    def get_items(self, **kwargs):
        deployment = getattr(g, 'deployment', None)
        if deployment:
            deployment_id = deployment.id
        else:
            deployment_id = None

        params = [Event.deployment_id == deployment_id]
        lower_cutoff = kwargs.get('from')
        upper_cutoff = kwargs.get('to')

        if lower_cutoff:
            try:
                params.append(Event.end >= lower_cutoff)
            except ValueError:
                return Event.query.filter(false())

        if upper_cutoff:
            try:
                params.append(Event.start <= upper_cutoff)
            except ValueError:
                return Event.query.filter(false())

        return Event.query.filter(*params)
