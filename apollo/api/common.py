# -*- coding: utf-8 -*-
from flask import jsonify
from flask_apispec import MethodResource, Ref, marshal_with, use_kwargs
from webargs import fields

from apollo.api.decorators import protect
from apollo.settings import API_PAGE_SIZE


@marshal_with(Ref("schema"))
class BaseListResource(MethodResource):
    schema = None

    @use_kwargs({"page": fields.Int(missing=1)}, location="query")
    @protect
    def get(self, **kwargs):
        page = kwargs.get("page")
        query_items = self.get_items(**kwargs)

        envelope = {
            "meta": {"page": page, "total": query_items.count()},
            "objects": self.schema.dump(query_items.paginate(page=page, per_page=API_PAGE_SIZE).items, many=True),
        }

        return jsonify(envelope)
