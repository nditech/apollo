# -*- coding: utf-8 -*-
import marshmallow as ma

from apollo.api.schema import BaseModelSchema
from apollo.formsframework.models import Form


class FormSchema(BaseModelSchema):
    form_type = ma.fields.Method('get_form_type')

    class Meta:
        model = Form
        fields = (
            'id', 'name', 'prefix', 'form_type', 'track_data_conflicts')

    def get_form_type(self, obj):
        return str(obj.form_type.value)
