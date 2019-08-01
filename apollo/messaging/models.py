# -*- coding: utf-8 -*-
from datetime import datetime

from flask_babelex import lazy_gettext as _
import sqlalchemy as sa
from sqlalchemy_utils import ChoiceType

from apollo.core import db
from apollo.dal.models import BaseModel


class Message(BaseModel):
    DIRECTIONS = (
        ('IN', _('INCOMING')),
        ('OUT', _('OUTGOING')),
    )

    MESSAGE_TYPES = (
        ('SMS', _('SMS')),
        ('API', _('API')),
        ('ODK', _('ODK')),
    )

    __tablename__ = 'message'

    id = db.Column(db.Integer, primary_key=True)
    direction = db.Column(ChoiceType(DIRECTIONS), nullable=False)
    recipient = db.Column(db.String)
    sender = db.Column(db.String)
    text = db.Column(db.String)
    message_type = db.Column(
        ChoiceType(MESSAGE_TYPES), default=MESSAGE_TYPES[0][0])
    received = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    delivered = db.Column(db.DateTime)
    deployment_id = db.Column(db.Integer, db.ForeignKey(
        'deployment.id', ondelete='CASCADE'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey(
        'event.id', ondelete='CASCADE'), nullable=False)
    submission_id = db.Column(
        db.Integer, db.ForeignKey('submission.id', ondelete='CASCADE'))
    participant_id = db.Column(
        db.Integer, db.ForeignKey('participant.id', ondelete='CASCADE'))
    # this is set only for reply SMS messages.
    originating_message_id = db.Column(
        db.Integer, db.ForeignKey('message.id', ondelete='SET NULL'))

    deployment = db.relationship(
        'Deployment',
        backref=db.backref(
            'messages', cascade='all, delete', passive_deletes=True))
    event = db.relationship(
        'Event', backref=db.backref(
            'messages', cascade='all, delete', passive_deletes=True))
    submission = db.relationship(
        'Submission', backref=db.backref('messages', passive_deletes=True))
    participant = db.relationship(
        'Participant', backref=db.backref('messages', passive_deletes=True))
    originating_message = db.relationship('Message', uselist=False)

    __table_args__ = (
        db.Index(
            'ix_text_tsv',
            sa.func.to_tsvector('english', text),
            postgresql_using='gin'),
    )
