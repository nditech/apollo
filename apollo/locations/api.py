# -*- coding: utf-8 -*-
from flask import current_app, jsonify
from flask_restful import Resource, fields, marshal, marshal_with
from flask_security import login_required
from apollo import services
from apollo.api.common import parser

LOCATION_TYPE_FIELD_MAPPER = {
    'id': fields.String,
    'name': fields.String,
}

LOCATION_FIELD_MAPPER = {
    'id': fields.String,
    'name': fields.String,
    'location_type': fields.String(
        attribute='location_type.name'
    ),
    'code': fields.String
}


class LocationTypeItemResource(Resource):
    @login_required
    def get(self, location_set_id, loc_type_id):
        # marshal() converts a custom object/dictionary/list using the mapper
        # into a Python dict
        data = marshal(
            services.location_types.fget_or_404(
                id=loc_type_id, location_set_id=location_set_id),
            LOCATION_TYPE_FIELD_MAPPER)

        # for the Url field, the constructor argument must be a full
        # path, because it will be converted using Flask's url_for(),
        # in the output() call, and if you don't give something it can
        # convert, it will fail with a BuildError
        # also, for a single item, you really don't need the url specced,
        # but whatever
        urlfield = fields.Url('locations.api.locationtype')
        data['uri'] = urlfield.output('uri', {'loc_type_id': data['id']})

        return jsonify(data)


class LocationTypeListResource(Resource):
    @login_required
    def get(self, location_set_id):
        # marshal() can also handle a list or tuple of objects, but it only
        # checks for a list or tuple, so we need to convert the queryset
        # to a list
        args = parser.parse_args()
        limit = min(
            args.get('limit') or current_app.config.get('PAGE_SIZE'),
            current_app.config.get('PAGE_SIZE'))
        offset = args.get('offset') or 0
        queryset = services.location_types.find(
            location_set_id=location_set_id)
        count = queryset.count()

        queryset = queryset.offset(offset).limit(limit)

        dataset = marshal(
            list(queryset),
            LOCATION_TYPE_FIELD_MAPPER
        )

        for d in dataset:
            urlfield = fields.Url('locations.api.locationtype')
            d['uri'] = urlfield.output('uri', {
                'loc_type_id': d['id'],
                'location_set_id': location_set_id})

        result = {
            'meta': {
                'limit': limit,
                'offset': offset,
                'total': count
            },
            'objects': dataset
        }

        return jsonify(result)


class LocationItemResource(Resource):
    @login_required
    @marshal_with(LOCATION_FIELD_MAPPER)
    def get(self, location_set_id, location_id):
        return jsonify(services.locations.fget_or_404(
            id=location_id, location_set_id=location_set_id))


class LocationListResource(Resource):
    @login_required
    def get(self, location_set_id):
        parser.add_argument('q', type=str)
        args = parser.parse_args()
        limit = min(
            args.get('limit') or current_app.config.get('PAGE_SIZE'),
            current_app.config.get('PAGE_SIZE'))
        offset = args.get('offset') or 0

        queryset = services.locations.find(location_set_id=location_set_id)
        count = queryset.count()

        # do location lookups
        # if 'q' in args and args.get('q'):
        #     queryset = queryset.filter(
        #         Q(name__icontains=args.get('q')) |
        #         Q(code__istartswith=args.get('q')) |
        #         Q(political_code__istartswith=args.get('q'))
        #     ).order_by('ancestor_count')

        queryset = queryset.limit(limit).offset(offset)

        dataset = marshal(
            list(queryset),
            LOCATION_FIELD_MAPPER
        )

        result = {
            'meta': {
                'limit': limit,
                'offset': offset,
                'total': count
            },
            'objects': dataset
        }

        return jsonify(result)
