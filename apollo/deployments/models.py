# -*- coding: utf-8 -*-
from datetime import datetime

from flask_babelex import lazy_gettext as _
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy_utils import ChoiceType

from apollo.constants import LANGUAGE_CHOICES
from apollo.core import db
from apollo.dal.models import BaseModel, Resource
from apollo.utils import current_timestamp


def _default_event_start():
    return datetime.combine(current_timestamp(), datetime.min.time())


def _default_event_end():
    return datetime.combine(current_timestamp(), datetime.max.time())


class Deployment(BaseModel):
    __tablename__ = 'deployment'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    hostnames = db.Column(ARRAY(db.String), nullable=False)
    allow_observer_submission_edit = db.Column(db.Boolean, default=True)
    logo = db.Column(db.String)
    include_rejected_in_votes = db.Column(db.Boolean, default=False)
    is_initialized = db.Column(db.Boolean, default=False)
    dashboard_full_locations = db.Column(db.Boolean, default=True)
    primary_locale = db.Column(db.String)
    other_locales = db.Column(ARRAY(db.String))

    @classmethod
    def find_by_hostname(cls, hostname):
        return cls.query.filter(cls.hostnames.any(hostname)).first()

    def __repr__(self):
        return str(self)

    def __str__(self):
        return self.name or ''

    @property
    def locale_codes(self):
        return [l.code for l in self.locales]


class Event(Resource):
    __mapper_args__ = {'polymorphic_identity': 'event'}
    __tablename__ = 'event'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    start = db.Column(
        db.DateTime(timezone=True), default=_default_event_start,
        nullable=False)
    end = db.Column(
        db.DateTime(timezone=True), default=_default_event_end,
        nullable=False)
    form_set_id = db.Column(
        db.Integer, db.ForeignKey('form_set.id', ondelete='SET NULL'))
    resource_id = db.Column(
        db.Integer, db.ForeignKey('resource.resource_id', ondelete='CASCADE'))
    location_set_id = db.Column(
        db.Integer, db.ForeignKey('location_set.id', ondelete='SET NULL'))
    participant_set_id = db.Column(
        db.Integer, db.ForeignKey('participant_set.id', ondelete='SET NULL'))
    form_set = db.relationship('FormSet', backref='events')
    location_set = db.relationship('LocationSet', backref='events')
    participant_set = db.relationship('ParticipantSet', backref='events')

    def __str__(self):
        return str(_('Event - %(name)s', name=self.name))
