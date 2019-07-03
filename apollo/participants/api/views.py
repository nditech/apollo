# -*- coding: utf-8 -*-
from flask import current_app, g, jsonify
from flask_apispec.views import MethodResourceMeta
from flask_restful import Resource, fields, marshal, marshal_with
from flask_security import login_required
from sqlalchemy import or_, text, bindparam

from apollo import services
from apollo.api.common import parser
from apollo.participants.models import Participant, ParticipantTranslations

PARTICIPANT_FIELD_MAPPER = {
    'id': fields.String,
    'name': fields.String,
    'participant_id': fields.String,
    'role': fields.String(attribute='role.name'),
}


class ParticipantItemResource(Resource, metaclass=MethodResourceMeta):
    @login_required
    @marshal_with(PARTICIPANT_FIELD_MAPPER)
    def get(self, participant_id):
        participant_set_id = g.event.participant_set_id
        return jsonify(services.participants.fget_or_404(
            id=participant_id, participant_set_id=participant_set_id))


class ParticipantListResource(Resource, metaclass=MethodResourceMeta):
    @login_required
    def get(self):
        parser.add_argument('q', type=str)
        args = parser.parse_args()
        limit = min(
            args.get('limit') or current_app.config.get('PAGE_SIZE'),
            current_app.config.get('PAGE_SIZE'))
        offset = args.get('offset') or 0
        participant_set_id = g.event.participant_set_id

        lookup_item = args.get('q')

        queryset = Participant.query.select_from(
            Participant, ParticipantTranslations).filter(
                Participant.participant_set_id == participant_set_id)

        if lookup_item:
            queryset = queryset.filter(
                or_(
                    text('translations.value ILIKE :name'),
                    Participant.participant_id.ilike(bindparam('pid'))
                )
            ).params(name=f'%{lookup_item}%', pid=f'{lookup_item}%')

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
