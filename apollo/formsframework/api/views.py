# -*- coding: utf-8 -*-
from flask_apispec import MethodResource, marshal_with, use_kwargs
from webargs import fields

from apollo.api.common import BaseListResource
from apollo.formsframework.api.schema import FormSchema
from apollo.formsframework.models import Form


@marshal_with(FormSchema)
class FormItemResource(MethodResource):
    def get(self, form_id, **kwargs):
        return Form.query.filter_by(id=form_id).one()


@use_kwargs({'form_type': fields.String()}, locations=['query'])
class FormListResource(BaseListResource):
    schema = FormSchema()

    def get_items(self, **kwargs):
        form_type = kwargs.get('form_type')
        if form_type:
            return Form.query.filter_by(form_type=form_type)

        return Form.query
