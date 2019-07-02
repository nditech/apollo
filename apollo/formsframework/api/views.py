# -*- coding: utf-8 -*-
from flask_apispec import MethodResource, marshal_with, use_kwargs
from webargs import fields

from apollo.formsframework.api.schema import FormSchema
from apollo.formsframework.models import Form


@marshal_with(FormSchema)
class FormItemResource(MethodResource):
    def get(self, form_id, **kwargs):
        return Form.query.filter_by(id=form_id).one()


@marshal_with(FormSchema(many=True))
class FormListResource(MethodResource):
    def get(self, **kwargs):
        return Form.query.all()
