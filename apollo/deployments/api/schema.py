# -*- coding: utf-8 -*-
from marshmallow import fields

from apollo.api.schema import BaseModelSchema
from apollo.deployments.models import Event


class EventSchema(BaseModelSchema):
    start = fields.Method(method_name='get_event_start')
    end = fields.Method(method_name='get_event_end')

    class Meta:
        model = Event
        fields = ('id', 'name', 'start', 'end')

    def get_event_start(self, obj):
        return obj.start.isoformat()

    def get_event_end(self, obj):
        return obj.end.isoformat()
