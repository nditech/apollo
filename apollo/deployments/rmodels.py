# -*- coding: utf-8 -*-
from datetime import datetime

from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy_utils import UUIDType

from apollo.core import db2
from apollo.dal.models import BaseModel


class Deployment(BaseModel):
    __tablename__ = 'deployments'

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

    start_date = db2.Column(db2.DateTime)
    end_date = db2.Column(db2.DateTime)
    deployment_id = db2.Column(UUIDType, db2.ForeignKey('deployments.id'))

    # ----- RELATIONSHIP PROPERTIES -----
    deployment = db2.relationship('Deployment', back_populates='events')
# from apollo.core import db
# from datetime import datetime
# from functools import partial
# 
# 
# class ParticipantPropertyName(db.StringField):
#     def validate(self, value):
#         from ..participants.models import Participant
#         if value in list(Participant._fields.keys()):
#             self.error(
#                 'String value cannot be one of the disallowed field names')
#         super(ParticipantPropertyName, self).validate(value)
# 
# 
# class CustomDataField(db.EmbeddedDocument):
#     name = ParticipantPropertyName()
#     label = db.StringField()
#     listview_visibility = db.BooleanField(default=False)
# 
#     def __str__(self):
#         return self.name or ''
# 
# 
# Deployment
# class Deployment(db.Document):
#     name = db.StringField(required=True)
#     hostnames = db.ListField(db.StringField())
#     administrative_divisions_graph = db.StringField()
#     participant_extra_fields = db.ListField(
#         db.EmbeddedDocumentField(CustomDataField))
#     allow_observer_submission_edit = db.BooleanField(
#         default=True,
#         verbose_name='Allow editing of Participant submissions?')
#     logo = db.StringField()
#     include_rejected_in_votes = db.BooleanField(default=False)
#     is_initialized = db.BooleanField(default=False)
#     dashboard_full_locations = db.BooleanField(
#         default=True,
#         verbose_name='Show all locations for dashboard stats?')
# 
#     meta = {
#         'indexes': [
#             ['hostnames']
#         ]
#     }
# 
#     def __str__(self):
#         return self.name or ''
# 
# 
# Event
# class Event(db.Document):
#     name = db.StringField()
#     start_date = db.DateTimeField(
#         default=partial(
#             datetime.combine, datetime.utcnow(), datetime.min.time()))
#     end_date = db.DateTimeField(
#         default=partial(
#             datetime.combine, datetime.utcnow(), datetime.max.time()))
# 
#     deployment = db.ReferenceField(Deployment)
# 
#     meta = {
#         'indexes': [
#             ['deployment', 'name'],
#             ['deployment', 'start_date', '-end_date']
#         ]
#     }
# 
#     def __str__(self):
#         return self.name or ''
