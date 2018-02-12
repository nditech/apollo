# -*- coding: utf-8 -*-
from datetime import datetime

from flask_babelex import lazy_gettext as _
from sqlalchemy_utils import ChoiceType

from apollo.core import db
from apollo.dal.models import BaseModel


class Message(BaseModel):
    DIRECTIONS = (
        (1, _('INCOMING')),
        (2, _('OUTGOING')),
    )

    __tablename__ = 'message'

    id = db.Column(db.Integer, db.Sequence('message_id_seq'), primary_key=True)
    direction = db.Column(ChoiceType(DIRECTIONS))
    recipient = db.Column(db.String)
    sender = db.Column(db.String)
    text = db.Column(db.String)
    received = db.Column(db.DateTime, default=datetime.utcnow)
    delivered = db.Column(db.DateTime)
    deployment_id = db.Column(db.Integer, db.ForeignKey('deployment.id'))
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    submission_id = db.Column(db.Integer, db.ForeignKey('submission.id'))

    # ----- RELATIONSHIP PROPERTIES ----
    deployment = db.relationship('Deployment', backref='messages')
    event = db.relationship('Event', backref='messages')
    submission = db.relationship('Submission')
