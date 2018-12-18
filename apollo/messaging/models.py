# -*- coding: utf-8 -*-
from datetime import datetime

from flask_babelex import lazy_gettext as _
from sqlalchemy_utils import ChoiceType

from apollo.core import db
from apollo.dal.models import BaseModel


class Message(BaseModel):
    DIRECTIONS = (
        ('IN', _('INCOMING')),
        ('OUT', _('OUTGOING')),
    )

    __tablename__ = 'message'

    id = db.Column(db.Integer, primary_key=True)
    direction = db.Column(ChoiceType(DIRECTIONS), nullable=False)
    recipient = db.Column(db.String)
    sender = db.Column(db.String)
    text = db.Column(db.String)
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

    # ----- RELATIONSHIP PROPERTIES ----
    deployment = db.relationship('Deployment', backref='messages')
    event = db.relationship('Event', backref='messages')
    submission = db.relationship('Submission', backref='messages')
    participant = db.relationship('Participant', backref='messages')
