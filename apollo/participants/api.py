# -*- coding: utf-8 -*-
from flask import current_app, g, jsonify
from flask_restful import Resource, fields, marshal, marshal_with
from flask_security import login_required
from sqlalchemy import or_

from apollo import services
from apollo.api.common import parser
from apollo.participants.models import Participant

PARTICIPANT_FIELD_MAPPER = {
    'id': fields.String,
    'name': fields.String,
    'participant_id': fields.String,
    'role': fields.String(attribute='role.name'),
}


class ParticipantItemResource(Resource):
    @login_required
    @marshal_with(PARTICIPANT_FIELD_MAPPER)
    def get(self, participant_id):
        participant_set_id = g.event.participant_set_id
        return jsonify(services.participants.fget_or_404(
            id=participant_id, participant_set_id=participant_set_id))


class ParticipantListResource(Resource):
    @login_required
    def get(self):
        parser.add_argument('q', type=str)
        args = parser.parse_args()
        limit = min(
            args.get('limit') or current_app.config.get('PAGE_SIZE'),
            current_app.config.get('PAGE_SIZE'))
        offset = args.get('offset') or 0
        participant_set_id = g.event.participant_set_id

        queryset = services.participants.find(
            participant_set_id=participant_set_id)

        lookup_item = args.get('q')
        if lookup_item:
            queryset = queryset.filter(or_(
                Participant.name.ilike('%{}%'.format(lookup_item)),
                Participant.participant_id.ilike('{}%'.format(lookup_item))
            ))

        count = queryset.count()
        queryset = queryset.limit(limit).offset(offset)

        dataset = marshal(
            list(queryset),
            PARTICIPANT_FIELD_MAPPER
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
