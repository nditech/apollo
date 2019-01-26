# -*- coding: utf-8 -*-
from flask import current_app, g, jsonify
from flask_restful import Resource, fields, marshal, marshal_with
from flask_security import login_required
from sqlalchemy import or_, text, bindparam

from ..api.common import parser
from .models import Location, LocationType, LocationTranslations

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
    def get(self, loc_type_id):
        # marshal() converts a custom object/dictionary/list using the mapper
        # into a Python dict
        location_set_id = getattr(g.event, 'location_id_set', None)
        data = marshal(
            LocationType.query.filter(
                LocationType.id == loc_type_id,
                LocationType.location_set_id == location_set_id
            ).first_or_404(),
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
    def get(self):
        # marshal() can also handle a list or tuple of objects, but it only
        # checks for a list or tuple, so we need to convert the queryset
        # to a list
        args = parser.parse_args()
        location_set_id = getattr(g.event, 'location_set_id', None)
        limit = min(
            args.get('limit') or current_app.config.get('PAGE_SIZE'),
            current_app.config.get('PAGE_SIZE'))
        offset = args.get('offset') or 0
        queryset = LocationType.query.filter(
            LocationType.location_set_id == location_set_id)
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
    def get(self, location_id):
        location_set_id = getattr(g.event, 'location_set_id', None)
        return jsonify(Location.query.filter(
            Location.id == location_id,
            Location.location_set_id == location_set_id).first_or_404())


class LocationListResource(Resource):
    @login_required
    def get(self):
        parser.add_argument('q', type=str)
        args = parser.parse_args()
        location_set_id = getattr(g.event, 'location_set_id', None)
        limit = min(
            args.get('limit') or current_app.config.get('PAGE_SIZE'),
            current_app.config.get('PAGE_SIZE'))
        offset = args.get('offset') or 0

        lookup_args = args.get('q')
        queryset = Location.query.select_from(
            Location, LocationTranslations).filter(
                Location.location_set_id == location_set_id)
        if lookup_args:
            queryset = queryset.filter(
                or_(
                    text('translations.value ILIKE :name'),
                    Location.code.ilike(bindparam('code'))
                )
            ).params(name=f'%{lookup_args}%', code=f'{lookup_args}%')
        count = queryset.count()

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
