# -*- coding: utf-8 -*-
from flask import jsonify
from flask_apispec import MethodResource, use_kwargs
from flask_restful import reqparse
from webargs import fields

from apollo.api.decorators import login_or_api_key_required
from apollo.settings import API_PAGE_SIZE

parser = reqparse.RequestParser()
parser.add_argument('limit', type=int)
parser.add_argument('offset', type=int)


class BaseListResource(MethodResource):
    schema = None

    @use_kwargs({'page': fields.Int(missing=1)})
    @login_or_api_key_required
    def get(self, **kwargs):
        page = kwargs.get('page')
        query_items = self.get_items(**kwargs)

        envelope = {
            'meta': {
                'page': page,
                'total': query_items.count()
            },
            'objects': self.schema.dump(
                query_items.paginate(page, per_page=API_PAGE_SIZE).items,
                many=True
            ).data
        }

        return jsonify(envelope)
