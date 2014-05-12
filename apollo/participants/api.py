from flask import current_app
from flask.ext.restful import Resource, fields, marshal
from .. import services
from ..api.common import parser

PARTICIPANT_FIELD_MAPPER = {
    'id': fields.String,
    'name': fields.String,
    'participant_id': fields.String,
}


class ParticipantItemResource(Resource):
    pass


class ParticipantListResource(Resource):
    def get(self):
        args = parser.parse_args()
        limit = args.get('limit') or current_app.config.get('PAGE_SIZE')
        offset = args.get('offset') or 0

        queryset = services.participants.find().limit(limit).skip(offset)

        dataset = marshal(
            list(queryset),
            PARTICIPANT_FIELD_MAPPER
        )

        meta = {'meta': {
            'limit': limit,
            'offset': offset,
            'total': queryset.count(False)
        }}

        dataset.append(meta)

        return dataset
