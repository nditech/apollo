from flask.ext.restful import Resource, fields, marshal
from .. import services

LOCATION_TYPE_FIELD_MAPPER = {
    'id': fields.String,
    'name': fields.String,
}


class LocationTypeItemResource(Resource):
    def get(self, loc_type_id):
        data = marshal(
            services.location_types.get_or_404(pk=loc_type_id),
            LOCATION_TYPE_FIELD_MAPPER)
        urlfield = fields.Url('locations.api.locationtype')
        data['uri'] = urlfield.output('uri', {'loc_type_id': data['id']})

        return data


class LocationTypeListResource(Resource):
    def get(self):
        dataset = marshal(
            list(services.location_types.find()),
            LOCATION_TYPE_FIELD_MAPPER
        )

        for d in dataset:
            urlfield = fields.Url('locations.api.locationtype')
            d['uri'] = urlfield.output('uri', {'loc_type_id': d['id']})

        return dataset
