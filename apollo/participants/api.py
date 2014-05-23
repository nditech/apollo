from flask import current_app
from flask.ext.restful import Resource, fields, marshal, marshal_with
from mongoengine import Q
from .. import services
from ..api.common import parser

PARTICIPANT_FIELD_MAPPER = {
    'id': fields.String,
    'name': fields.String,
    'participant_id': fields.String,
    'role': fields.String,
}


class ParticipantItemResource(Resource):
    @marshal_with(PARTICIPANT_FIELD_MAPPER)
    def get(self, participant_id):
        return services.participants.get_or_404(pk=participant_id)


class ParticipantListResource(Resource):
    def get(self):
        parser.add_argument('q', type=str)
        args = parser.parse_args()
        limit = args.get('limit') or current_app.config.get('PAGE_SIZE')
        offset = args.get('offset') or 0

        queryset = services.participants.find()

        # do location lookups
        if 'q' in args and args.get('q'):
            queryset = queryset.filter(
                Q(name__icontains=args.get('q')) |
                Q(participant_id__istartswith=args.get('q'))
            )

        queryset = queryset.limit(limit).skip(offset)

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
