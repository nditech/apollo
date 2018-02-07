# -*- coding: utf-8 -*-
from flask_babelex import lazy_gettext as _
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy_utils import ChoiceType

from apollo.core import db2
from apollo.dal.models import BaseModel
from apollo.utils import current_timestamp


class Submission(BaseModel):
    SUBMISSION_TYPES = (
        ('O', _('Observer submission')),
        ('M', _('Master submission')),
    )

    __tablename__ = 'submission'

    id = db2.Column(
        db2.Integer, db2.Sequence('submission_id_seq'), primary_key=True)
    deployment_id = db2.Column(db2.Integer, db2.ForeignKey('deployment.id'))
    event_id = db2.Column(db2.Integer, db2.ForeignKey('event.id'))
    form_id = db2.Column(db2.Integer, db2.ForeignKey('form.id'))
    participant_id = db2.Column(db2.Integer, db2.ForeignKey('participant.id'))
    location_id = db2.Column(db2.Integer, db2.ForeignKey('location.id'))
    data = db2.Column(JSONB)
    submission_type = db2.Column(ChoiceType(SUBMISSION_TYPES))
    created = db2.Column(db2.DateTime)
    updated = db2.Column(db2.DateTime)
    sender_verified = db2.Column(db2.Boolean, default=True)
    deployment = db2.relationship('Deployment', backref='submissions')
    event = db2.relationship('Event', backref='submissions')
    form = db2.relationship('Form', backref='submissions')
    location = db2.relationship('Location', backref='submissions')
    participant = db2.relationship('Participant', backref='submissions')


class SubmissionComment(BaseModel):
    __tablename__ = 'submission_comment'

    id = db2.Column(
        db2.Integer, db2.Sequence('submmision_comment_id_seq'),
        primary_key=True)
    submission_id = db2.Column(db2.Integer, db2.ForeignKey('submission.id'))
    submission = db2.relationship('Submission', backref='comments')
    user_id = db2.Column(db2.Integer, db2.ForeignKey('user.id'))
    user = db2.relationship('User', backref='submission_comments')
    comment = db2.Column(db2.String)
    submit_date = db2.Column(db2.DateTime, default=current_timestamp)
    deployment_id = db2.Column(db2.Integer, db2.ForeignKey('deployment.id'))
    deployment = db2.relationship('Deployment', backref='submission_comments')


class SubmissionVersion(BaseModel):
    __tablename__ = 'submission_version'

    CHANNEL_CHOICES = (
        ('SMS', _('SMS')),
        ('WEB', _('Web')),
        ('API', _('API')),
        ('ODK', _('ODK')),
    )
    id = db2.Column(
        db2.Integer, db2.Sequence('submmision_version_id_seq'),
        primary_key=True)
    submission_id = db2.Column(db2.Integer, db2.ForeignKey('submission.id'))
    submission = db2.relationship('Submission', backref='versions')
    timestamp = db2.Column(db2.DateTime, default=current_timestamp)
    channel = db2.Column(ChoiceType(CHANNEL_CHOICES))
    deployment_id = db2.Column(db2.Integer, db2.ForeignKey('deployment.id'))
    deployment = db2.relationship('Deployment', backref='submission_versions')
    identity = db2.Column(db2.String, default='unknown', nullable=False)
