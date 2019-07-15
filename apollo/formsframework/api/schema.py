# -*- coding: utf-8 -*-
import marshmallow as ma

from apollo.api.schema import BaseModelSchema
from apollo.formsframework.models import Form


class FormSchema(BaseModelSchema):
    events = ma.fields.Method('get_event_ids')
    form_type = ma.fields.Method('get_form_type')

    class Meta:
        model = Form
        fields = (
            'id', 'name', 'prefix', 'form_type', 'track_data_conflicts',
            'events', 'data')

    def get_event_ids(self, obj):
        return [ev.id for ev in obj.events]

    def get_form_type(self, obj):
        return str(obj.form_type.code)
