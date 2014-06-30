from flask.ext.restful import Resource, fields, marshal_with
from .. import services


SIMPLE_FORM_ITEM_MAPPER = {
    'name': fields.String,
}


class SimpleFormItemResource(Resource):
    @marshal_with(SIMPLE_FORM_ITEM_MAPPER)
    def get(self, form_pk):
        return services.forms.get_or_404(pk=form_pk)
