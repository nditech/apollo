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
            'id', 'name', 'prefix', 'form_type', 'untrack_data_conflicts',
            'events', 'data')

    def get_event_ids(self, obj):
        return [ev.id for ev in obj.events]

    def get_form_type(self, obj):
        return str(obj.form_type.code)


class CriterionSchema(ma.Schema):
    lvalue = ma.fields.String(required=True)
    comparator = ma.fields.String(required=True)
    rvalue = ma.fields.String(required=True)
    conjunction = ma.fields.String(required=True)


class QualityCheckSchema(ma.Schema):
    name = ma.fields.String(required=True)
    description = ma.fields.String(required=True)
    criteria = ma.fields.List(ma.fields.Nested(CriterionSchema))
