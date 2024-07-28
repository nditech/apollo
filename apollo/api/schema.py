# -*- coding: utf-8 -*-
from marshmallow import EXCLUDE
from marshmallow_sqlalchemy import SQLAlchemySchema, SQLAlchemySchemaOpts

from apollo.core import db


class BaseSchemaOptions(SQLAlchemySchemaOpts):
    '''
    Base options class for model schemas
    '''
    def __init__(self, meta, ordered=False):
        if not hasattr(meta, 'sqla_session'):
            meta.sqla_session = db.session
        meta.unknown = EXCLUDE
        super(BaseSchemaOptions, self).__init__(meta, ordered=ordered)


class BaseModelSchema(SQLAlchemySchema):
    '''
    Base model schema
    '''
    OPTIONS_CLASS = BaseSchemaOptions
