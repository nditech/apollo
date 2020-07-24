# -*- coding: utf-8 -*-
from datetime import datetime

from flask_babelex import gettext
from sqlalchemy import and_, or_
from sqlalchemy.dialects.postgresql import ARRAY

from apollo.constants import LANGUAGES
from apollo.core import db
from apollo.dal.models import BaseModel, Resource
from apollo.utils import current_timestamp

import pytz


def _default_event_start():
    return pytz.utc.localize(
        datetime.combine(current_timestamp(), datetime.min.time()))


def _default_event_end():
    return pytz.utc.localize(
        datetime.combine(current_timestamp(), datetime.max.time()))


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
    enable_partial_response_for_messages = db.Column(db.Boolean, default=True)
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
        locales = [self.primary_locale] if self.primary_locale else ['en']
        if self.other_locales:
            locales.extend(self.other_locales)

        return locales

    @property
    def languages(self):
        return {
            locale: name
            for locale, name in LANGUAGES.items()
            if locale in self.locale_codes
        }


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
    resource_id = db.Column(
        db.Integer, db.ForeignKey('resource.resource_id', ondelete='CASCADE'))
    location_set_id = db.Column(
        db.Integer, db.ForeignKey('location_set.id', ondelete='SET NULL'))
    participant_set_id = db.Column(
        db.Integer, db.ForeignKey('participant_set.id', ondelete='SET NULL'))
    location_set = db.relationship('LocationSet', backref='events')
    participant_set = db.relationship('ParticipantSet', backref='events')

    def __str__(self):
        return gettext('Event - %(name)s', name=self.name)

    @classmethod
    def overlapping_events(cls, event, timestamp=None):
        # return events overlapping with the specified event at
        # the current or specified time, or return the specified event
        # as a query
        if timestamp is None:
            timestamp = current_timestamp()

        cond1 = cls.start <= timestamp
        cond2 = cls.end >= timestamp
        cond3 = cls.id == event.id
        term = and_(cond1, cond2)

        return cls.query.filter(or_(term, cond3))
