# -*- coding: utf-8 -*-
from apollo.api.schema import BaseModelSchema
from apollo.deployments.models import Event


class EventSchema(BaseModelSchema):
    class Meta:
        model = Event
        fields = ('id', 'name', 'start', 'end')
