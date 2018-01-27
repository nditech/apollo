# -*- coding: utf-8 -*-
from sqlalchemy.dialects.postgresql import ARRAY

from apollo.core import db2
from apollo.dal.models import BaseModel


class Sample(BaseModel):
    __tablename__ = 'samples'

    id = db2.Column(
        db2.Integer, db2.Sequence('sample_id_seq'), primary_key=True)
    name = db2.Column(db2.String)
    deployment_id = db2.Column(db2.Integer, db2.ForeignKey('deployments.id'))


class LocationType(BaseModel):
    __tablename__ = 'location_types'

    id = db2.Column(
        db2.Integer, db2.Sequence('location_type_id_seq'), primary_key=True)
    name = db2.Column(db2.String)
    ancestors_ref = db2.Column(ARRAY(db2.Integer))
    is_administrative = db2.Column(db2.Boolean, default=False)
    is_political = db2.Column(db2.Boolean, default=False)
    has_registered_voters = db2.Column(db2.Boolean, default=False)
    has_political_code = db2.Column(db2.Boolean, default=False)
    has_other_code = db2.Column(db2.Boolean, default=False)
    slug = db2.Column(db2.String)
    deployment_id = db2.Column(db2.Integer, db2.ForeignKey('deployments.id'))


class Location(BaseModel):
    __tablename__ = 'locations'

    id = db2.Column(
        db2.Integer, db2.Sequence('location_id_seq'), primary_key=True)
    name = db2.Column(db2.String)
    code = db2.Column(db2.String)
    political_code = db2.Column(db2.String)
    other_code = db2.Column(db2.String)
    ancestors_ref = db2.Column(ARRAY(db2.Integer))
    registered_voters = db2.Column(db2.Integer, default=0)
    deployment_id = db2.Column(db2.Integer, db2.ForeignKey('deployments.id'))
