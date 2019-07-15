# -*- coding: utf-8 -*-
from marshmallow_sqlalchemy import ModelSchema, ModelSchemaOpts

from apollo.core import db


class BaseSchemaOptions(ModelSchemaOpts):
    '''
    Base options class for model schemas
    '''
    def __init__(self, meta):
        if not hasattr(meta, 'sqla_session'):
            meta.sqla_session = db.session
            super().__init__(meta)


class BaseModelSchema(ModelSchema):
    '''
    Base model schema
    '''
    OPTIONS_CLASS = BaseSchemaOptions
