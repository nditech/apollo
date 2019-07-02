# -*- coding: utf-8 -*-
from flask_apispec import MethodResource, use_kwargs
from flask_restful import reqparse
from webargs import fields

from apollo.settings import API_PAGE_SIZE

parser = reqparse.RequestParser()
parser.add_argument('limit', type=int)
parser.add_argument('offset', type=int)


class BaseListResource(MethodResource):
    @use_kwargs({'page': fields.Int(missing=1)})
    def get(self, **kwargs):
        page = kwargs.get('page')

        return self.get_items(**kwargs).paginate(
            page, per_page=API_PAGE_SIZE).items
