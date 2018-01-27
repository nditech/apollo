# -*- coding: utf-8 -*-
from datetime import datetime

from sqlalchemy.dialects.postgresql import ARRAY, JSONB

from apollo.core import db2
from apollo.dal.models import BaseModel


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

    # ----- RELATIONSHIP PROPERTIES -----
    events = db2.relationship('Event', back_populates='deployment')

    def __str__(self):
        return self.name or ''


class Event(BaseModel):
    __tablename__ = 'events'

    id = db2.Column(
        db2.Integer, db2.Sequence('event_id_seq'), primary_key=True)
    start_date = db2.Column(db2.DateTime)
    end_date = db2.Column(db2.DateTime)
    deployment_id = db2.Column(db2.Integer, db2.ForeignKey('deployments.id'))

    # ----- RELATIONSHIP PROPERTIES -----
    deployment = db2.relationship('Deployment', back_populates='events')
