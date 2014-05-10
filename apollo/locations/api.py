from flask import request
from flask.ext.restful import (
    Resource, fields as fields, marshal, marshal_with
)
from .. import services

DEFAULT_PAGE_SIZE = 25

LOCATION_TYPE_FIELD_MAPPER = {
    'id': fields.String,
    'name': fields.String,
}

LOCATION_FIELD_MAPPER = {
    'id': fields.String,
    'name': fields.String,
    'location_type': fields.String
}


class LocationTypeItemResource(Resource):
    def get(self, loc_type_id):
        # marshal() converts a custom object/dictionary/list using the mapper
        # into a Python dict
        data = marshal(
            services.location_types.get_or_404(pk=loc_type_id),
            LOCATION_TYPE_FIELD_MAPPER)

        # for the Url field, the constructor argument must be a full
        # path, because it will be converted using Flask's url_for(),
        # in the output() call, and if you don't give something it can
        # convert, it will fail with a BuildError
        # also, for a single item, you really don't need the url specced,
        # but whatever
        urlfield = fields.Url('locations.api.locationtype')
        data['uri'] = urlfield.output('uri', {'loc_type_id': data['id']})

        return data


class LocationTypeListResource(Resource):
    def get(self):
        # marshal() can also handle a list or tuple of objects, but it only
        # checks for a list or tuple, so we need to convert the queryset
        # to a list
        dataset = marshal(
            list(services.location_types.find()),
            LOCATION_TYPE_FIELD_MAPPER
        )

        for d in dataset:
            urlfield = fields.Url('locations.api.locationtype')
            d['uri'] = urlfield.output('uri', {'loc_type_id': d['id']})

        return dataset


class LocationItemResource(Resource):
    @marshal_with(LOCATION_FIELD_MAPPER)
    def get(self, location_id):
        return services.locations.get_or_404(pk=location_id)


class LocationListResource(Resource):
    def get(self):
        kwargs = request.args.copy()
        try:
            offset = int(kwargs.pop('offset', 0))
        except ValueError:
            offset = 0

        try:
            limit = int(kwargs.pop('limit', DEFAULT_PAGE_SIZE))
        except ValueError:
            limit = DEFAULT_PAGE_SIZE

        queryset = services.locations.find().limit(limit).skip(offset)

        # do location name lookups
        if 'name__startswith' in kwargs:
            queryset = queryset(
                name__istartswith=kwargs.pop('name__startswith')
            )

        dataset = marshal(
            list(queryset),
            LOCATION_FIELD_MAPPER
        )

        meta = {
            'limit': limit,
            'offset': offset,
            'total': queryset.count(False)
        }

        dataset.append(meta)

        return dataset
