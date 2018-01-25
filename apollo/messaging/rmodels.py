# -*- coding: utf-8 -*-
from datetime import datetime
# from apollo.core import db
# from apollo.deployments.models import Deployment, Event
# from apollo.participants.models import Participant
# from apollo.submissions.models import Submission
# 
# 
# class Message(db.Document):
#     DIRECTIONS = (
#         ('IN', 'INCOMING'),
#         ('OUT', 'OUTGOING'))
# 
#     direction = db.StringField(choices=DIRECTIONS)
#     recipient = db.StringField()
#     sender = db.StringField()
#     text = db.StringField()
#     participant = db.ReferenceField(Participant)
#     submission = db.ReferenceField(Submission)
#     received = db.DateTimeField(default=datetime.utcnow)
#     delivered = db.DateTimeField()
# 
#     deployment = db.ReferenceField(Deployment)
#     event = db.ReferenceField(Event)
# 
#     meta = {
#         'indexes': [
#             ['sender'],
#             ['recipient'],
#             ['text'],
#             ['participant'],
#             ['submission'],
#             ['received'],
#             ['delivered'],
#             ['deployment'],
#             ['deployment', 'event']
#         ]
#     }
from babel import lazy_gettext as _
from sqlalchemy_utils import ChoiceType, UUIDType

from apollo.core import db2
from apollo.dal.models import BaseModel


class Message(BaseModel):
    DIRECTIONS = (
        (1, _('INCOMING')),
        (2, _('OUTGOING')),
    )

    __tablename__ = 'messages'

    direction = db2.Column(ChoiceType(DIRECTIONS))
    recipient = db2.Column(db2.String)
    sender = db2.Column(db2.String)
    text = db2.Column(db2.String)
    received = db2.Column(db2.DateTime, default=datetime.utcnow)
    delivered = db2.Column(db2.DateTime)
    deployment_id = db2.Column(UUIDType, db2.ForeignKey('deployments.id'))
    event_id = db2.Column(UUIDType, db2.ForeignKey('events.id'))

    # ----- RELATIONSHIP PROPERTIES ----
    deployment = db2.relationship('Deployment', back_populates='messages')
    event = db2.relationship('Event', back_populates='messages')
