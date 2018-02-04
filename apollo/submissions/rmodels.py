# -*- coding: utf-8 -*-
from flask_babelex import lazy_gettext as _
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy_utils import ChoiceType

from apollo.core import db2
from apollo.dal.models import BaseModel


class Submission(BaseModel):
    __tablename__ = 'submissions'

    id = db2.Column(
        db2.Integer, db2.Sequence('submission_id_seq'), primary_key=True)
    deployment_id = db2.Column(db2.Integer, db2.ForeignKey('deployments.id'))
    event_id = db2.Column(db2.Integer, db2.ForeignKey('events.id'))
    form_id = db2.Column(db2.Integer, db2.ForeignKey('forms.id'))
    participant_id = db2.Column(db2.Integer, db2.ForeignKey('participants.id'))
    location_id = db2.Column(db2.Integer, db2.ForeignKey('locations.id'))
    data = db2.Column(JSONB)
    created = db2.Column(db2.DateTime)
    updated = db2.Column(db2.DateTime)
    sender_verified = db2.Column(db2.Boolean, default=True)
