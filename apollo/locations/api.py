from flask import current_app
from flask.ext.restful import Resource, fields, marshal, marshal_with
from mongoengine import Q
from .. import services
from ..api.common import parser

LOCATION_TYPE_FIELD_MAPPER = {
    'id': fields.String,
    'name': fields.String,
}

LOCATION_FIELD_MAPPER = {
    'id': fields.String,
    'name': fields.String,
    'location_type': fields.String,
    'code': fields.String
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
        args = parser.parse_args()
        limit = min(
            args.get('limit') or current_app.config.get('PAGE_SIZE'),
            current_app.config.get('PAGE_SIZE'))
        offset = args.get('offset') or 0
        queryset = services.location_types.find().skip(offset).limit(limit)

        dataset = marshal(
            list(queryset),
            LOCATION_TYPE_FIELD_MAPPER
        )

        for d in dataset:
            urlfield = fields.Url('locations.api.locationtype')
            d['uri'] = urlfield.output('uri', {'loc_type_id': d['id']})

        meta = {'meta': {
            'limit': limit,
            'offset': offset,
            'total': queryset.count(False)
        }}

        dataset.append(meta)

        return dataset


class LocationItemResource(Resource):
    @marshal_with(LOCATION_FIELD_MAPPER)
    def get(self, location_id):
        return services.locations.get_or_404(pk=location_id)


class LocationListResource(Resource):
    def get(self):
        parser.add_argument('q', type=str)
        args = parser.parse_args()
        limit = min(
            args.get('limit') or current_app.config.get('PAGE_SIZE'),
            current_app.config.get('PAGE_SIZE'))
        offset = args.get('offset') or 0

        queryset = services.locations.find()

        # do location lookups
        if 'q' in args and args.get('q'):
            queryset = queryset.filter(
                Q(name__icontains=args.get('q')) |
                Q(code__istartswith=args.get('q')) |
                Q(political_code__istartswith=args.get('q'))
            )

        queryset = queryset.limit(limit).skip(offset)

        dataset = marshal(
            list(queryset),
            LOCATION_FIELD_MAPPER
        )

        meta = {'meta': {
            'limit': limit,
            'offset': offset,
            'total': queryset.count(False)
        }}

        dataset.append(meta)

        return dataset
