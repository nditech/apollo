from flask import request
from flask.ext.restful import Resource, fields, marshal
from .. import services
from ..api.common import get_limit, get_offset

PARTICIPANT_FIELD_MAPPER = {
    'id': fields.String,
    'name': fields.String,
    'participant_id': fields.String,
}


class ParticipantItemResource(Resource):
    pass


class ParticipantListResource(Resource):
    def get(self):
        limit = get_limit(request.args)
        offset = get_offset(request.args)

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
