# -*- coding: utf-8 -*-
from datetime import datetime, timezone
import sys

from dateutil.parser import parse
from flask_apispec import MethodResource, marshal_with, use_kwargs
from sqlalchemy import false
from webargs import fields

from apollo.api.common import BaseListResource
from apollo.deployments.api.schema import EventSchema
from apollo.deployments.models import Event

EVENT_LIST_QUERY_MAP = {
    # the timestamp to start filtering events from as an ISO 8601 format string
    'from': fields.Str(),
    # the timestamp to stop filtering events to as an ISO 8601 format string
    'to': fields.Str(),
}


class EventItemResource(MethodResource):
    @marshal_with(EventSchema)
    def get(self, event_id):
        return Event.query.filter_by(id=event_id).one()


@use_kwargs(EVENT_LIST_QUERY_MAP)
class EventListResource(BaseListResource):
    schema = EventSchema()

    def get_items(self, **kwargs):
        params = []
        lower_cutoff = kwargs.get('from')
        upper_cutoff = kwargs.get('to')

        if lower_cutoff:
            try:
                lower_timestamp = parse(lower_cutoff)

                params.append(Event.end >= lower_timestamp)
            except ValueError:
                return Event.query.filter(false())

        if upper_cutoff:
            try:
                upper_timestamp = parse(upper_cutoff)

                params.append(Event.start <= upper_timestamp)
            except ValueError:
                return Event.query.filter(false())

        return Event.query.filter(*params)
