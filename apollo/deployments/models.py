# -*- coding: utf-8 -*-
from datetime import datetime

from sqlalchemy.dialects.postgresql import ARRAY, JSONB

from apollo.core import db
from apollo.dal.models import BaseModel, Resource
from apollo.utils import current_timestamp


def _default_event_start():
    return datetime.combine(current_timestamp(), datetime.min.time())


def _default_event_end():
    return datetime.combine(current_timestamp(), datetime.max.time())


class Deployment(BaseModel):
    __tablename__ = 'deployment'

    id = db.Column(
        db.Integer, db.Sequence('deployment_id_seq'), primary_key=True)
    name = db.Column(db.String, nullable=False)
    hostnames = db.Column(ARRAY(db.String))
    allow_observer_submission_edit = db.Column(db.Boolean, default=True)
    logo_filename = db.Column(db.String)
    logo_url = db.Column(db.String)
    include_rejected_in_votes = db.Column(db.Boolean, default=False)
    is_initialized = db.Column(db.Boolean, default=False)
    dashboard_full_locations = db.Column(db.Boolean, default=True)

    @classmethod
    def find_by_hostname(cls, hostname):
        return cls.query.filter(cls.hostnames.any(hostname)).first_or_404()

    def __str__(self):
        return self.name or ''


class FormSet(BaseModel):
    __tablename__ = 'form_set'

    id = db.Column(
        db.Integer, db.Sequence('form_set_id_seq'), primary_key=True)
    name = db.Column(db.String)
    slug = db.Column(db.String)
    deployment_id = db.Column(db.Integer, db.ForeignKey('deployment.id'))
    deployment = db.relationship('Deployment', backref='form_sets')


class LocationSet(BaseModel):
    __tablename__ = 'location_set'

    id = db.Column(
        db.Integer, db.Sequence('location_set_id_seq'), primary_key=True)
    name = db.Column(db.String)
    slug = db.Column(db.String)
    deployment_id = db.Column(db.Integer, db.ForeignKey('deployment.id'))
    deployment = db.relationship('Deployment', backref='location_sets')


class ParticipantSet(BaseModel):
    __tablename__ = 'participant_set'

    id = db.Column(
        db.Integer, db.Sequence('participant_set_id_seq'), primary_key=True)
    name = db.Column(db.String)
    slug = db.Column(db.String)
    deployment_id = db.Column(db.Integer, db.ForeignKey('deployment.id'))
    deployment = db.relationship('Deployment', backref='participant_sets')
    extra_fields = db.Column(JSONB)


class Event(Resource):
    __mapper_args__ = {'polymorphic_identity': 'event'}
    __tablename__ = 'event'

    id = db.Column(
        db.Integer, db.Sequence('event_id_seq'), primary_key=True)
    name = db.Column(db.String)
    start = db.Column(db.DateTime, default=_default_event_start)
    end = db.Column(db.DateTime, default=_default_event_end)
    deployment_id = db.Column(db.Integer, db.ForeignKey('deployment.id'))
    form_set_id = db.Column(db.Integer, db.ForeignKey('form_set.id'))
    resource_id = db.Column(
        db.Integer, db.ForeignKey('resource.resource_id'))
    location_set_id = db.Column(
        db.Integer, db.ForeignKey('location_set.id'))
    participant_set_id = db.Column(
        db.Integer, db.ForeignKey('participant_set.id'))
    deployment = db.relationship('Deployment', backref='events')
    form_set = db.relationship('FormSet', backref='events')
    location_set = db.relationship('LocationSet', backref='events')
    participant_set = db.relationship('ParticipantSet', backref='events')

    def __str__(self):
        return self.name
