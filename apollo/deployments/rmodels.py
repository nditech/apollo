# -*- coding: utf-8 -*-
from datetime import datetime

from pytz import utc
from sqlalchemy.dialects.postgresql import ARRAY

from apollo.core import db2
from apollo.dal.models import BaseModel


def _default_event_start():
    return datetime.combine(
        utc.localize(datetime.utcnow()),
        datetime.min.time())


def _default_event_end():
    return datetime.combine(
        utc.localize(datetime.utcnow()),
        datetime.max.time())


class Deployment(BaseModel):
    __tablename__ = 'deployments'

    id = db2.Column(
        db2.Integer, db2.Sequence('deployment_id_seq'), primary_key=True)
    name = db2.Column(db2.String, nullable=False)
    hostnames = db2.Column(ARRAY(db2.String))
    allow_observer_submission_edit = db2.Column(db2.Boolean, default=True)
    logo = db2.Column(db2.String)
    include_rejected_in_votes = db2.Column(db2.Boolean, default=False)
    is_initialized = db2.Column(db2.Boolean, default=False)
    dashboard_full_locations = db2.Column(db2.Boolean, default=True)

    def __str__(self):
        return self.name or ''


class FormSet(BaseModel):
    __tablename__ = 'form_sets'

    id = db2.Column(
        db2.Integer, db2.Sequence('form_set_id_seq'), primary_key=True)
    name = db2.Column(db2.String)
    slug = db2.Column(db2.String)
    deployment_id = db2.Column(db2.Integer, db2.ForeignKey('deployments.id'))
    deployment = db2.relationship('Deployment', backref='form_sets')


class LocationSet(BaseModel):
    __tablename__ = 'location_sets'

    id = db2.Column(
        db2.Integer, db2.Sequence('location_set_id_seq'), primary_key=True)
    name = db2.Column(db2.String)
    slug = db2.Column(db2.String)
    deployment_id = db2.Column(db2.Integer, db2.ForeignKey('deployments.id'))
    deployment = db2.relationship('Deployment', backref='location_sets')


class ParticipantSet(BaseModel):
    __tablename__ = 'participant_sets'

    id = db2.Column(
        db2.Integer, db2.Sequence('participant_set_id_seq'), primary_key=True)
    name = db2.Column(db2.String)
    slug = db2.Column(db2.String)
    deployment_id = db2.Column(db2.Integer, db2.ForeignKey('deployments.id'))
    deployment = db2.relationship('Deployment', backref='participant_sets')


class Event(BaseModel):
    __tablename__ = 'events'

    id = db2.Column(
        db2.Integer, db2.Sequence('event_id_seq'), primary_key=True)
    start = db2.Column(db2.DateTime, default=_default_event_start)
    end = db2.Column(db2.DateTime, default=_default_event_end)
    deployment_id = db2.Column(db2.Integer, db2.ForeignKey('deployments.id'))
    form_set_id = db2.Column(db2.Integer, db2.ForeignKey('form_sets.id'))
    location_set_id = db2.Column(
        db2.Integer, db2.ForeignKey('location_sets.id'))
    participant_set_id = db2.Column(
        db2.Integer, db2.ForeignKey('participant_sets.id'))
    deployment = db2.relationship('Deployment', backref='events')
    form_set = db2.relationship('FormSet', backref='events')
    location_set = db2.relationship('LocationSet', backref='events')
    participant_set = db2.relationship('ParticipantSet', backref='events')

    def __str__(self):
        return self.name
