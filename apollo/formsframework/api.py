# -*- coding: utf-8 -*-
from flask_restful import Resource, fields, marshal_with
from flask_security import login_required
from apollo import services


SIMPLE_FORM_ITEM_MAPPER = {
    'name': fields.String,
}


class SimpleFormItemResource(Resource):
    @login_required
    @marshal_with(SIMPLE_FORM_ITEM_MAPPER)
    def get(self, form_pk):
        return services.forms.get_or_404(pk=form_pk)
