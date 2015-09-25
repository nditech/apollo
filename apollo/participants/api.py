from flask import current_app, jsonify
from flask.ext.restful import Resource, fields, marshal, marshal_with
from flask.ext.security import login_required
from mongoengine import Q
from apollo import services
from apollo.api.common import parser

PARTICIPANT_FIELD_MAPPER = {
    'id': fields.String,
    'name': fields.String,
    'participant_id': fields.String,
    'role': fields.String,
}


class ParticipantItemResource(Resource):
    @login_required
    @marshal_with(PARTICIPANT_FIELD_MAPPER)
    def get(self, participant_id):
        return jsonify(services.participants.get_or_404(pk=participant_id))


class ParticipantListResource(Resource):
    @login_required
    def get(self):
        parser.add_argument('q', type=unicode)
        args = parser.parse_args()
        limit = min(
            args.get('limit') or current_app.config.get('PAGE_SIZE'),
            current_app.config.get('PAGE_SIZE'))
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

        result = {
            'meta': {
                'limit': limit,
                'offset': offset,
                'total': queryset.count(False)
            },
            'objects': dataset
        }

        return jsonify(result)
