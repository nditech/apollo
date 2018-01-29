# -*- coding: utf-8 -*-
from datetime import datetime

from flask_babel import lazy_gettext as _
from sqlalchemy_utils import ChoiceType

from apollo.core import db2
from apollo.dal.models import BaseModel


class Message(BaseModel):
    DIRECTIONS = (
        (1, _('INCOMING')),
        (2, _('OUTGOING')),
    )

    __tablename__ = 'messages'

    id = db2.Column(db2.Integer, db2.Sequence('message_id_seq'), primary_key=True)
    direction = db2.Column(ChoiceType(DIRECTIONS))
    recipient = db2.Column(db2.String)
    sender = db2.Column(db2.String)
    text = db2.Column(db2.String)
    received = db2.Column(db2.DateTime, default=datetime.utcnow)
    delivered = db2.Column(db2.DateTime)
    deployment_id = db2.Column(db2.Integer, db2.ForeignKey('deployments.id'))
    event_id = db2.Column(db2.Integer, db2.ForeignKey('events.id'))

    # ----- RELATIONSHIP PROPERTIES ----
    deployment = db2.relationship('Deployment', back_populates='messages')
    event = db2.relationship('Event', back_populates='messages')
