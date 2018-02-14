# -*- coding: utf-8 -*-
from flask_babelex import lazy_gettext as _
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy_utils import ChoiceType

from apollo.core import db
from apollo.dal.models import BaseModel
from apollo.utils import current_timestamp

FLAG_STATUSES = {
    'no_problem': ('0', _('No Problem')),
    'problem': ('2', _('Problem')),
    'verified': ('4', _('Verified')),
    'rejected': ('5', _('Rejected'))
}

QUALITY_STATUSES = {
    'OK': '0',
    'FLAGGED': '2',
    'VERIFIED': '3'
}

FLAG_CHOICES = (
    ('0', _('OK')),
    ('-1', _('MISSING')),
    ('2', _('FLAGGED')),
    ('4', _('VERIFIED')),
    ('5', _('REJECTED'))
)

STATUS_CHOICES = (
    ('', _('Status')),
    ('0', _('Status — No Problem')),
    ('2', _('Status — Unverified')),
    ('4', _('Status — Verified')),
    ('5', _('Status — Rejected'))
)


class Submission(BaseModel):
    SUBMISSION_TYPES = (
        ('O', _('Observer submission')),
        ('M', _('Master submission')),
    )

    __tablename__ = 'submission'

    id = db.Column(
        db.Integer, db.Sequence('submission_id_seq'), primary_key=True)
    deployment_id = db.Column(
        db.Integer, db.ForeignKey('deployment.id'), nullable=False)
    event_id = db.Column(
        db.Integer, db.ForeignKey('event.id'), nullable=False)
    form_id = db.Column(db.Integer, db.ForeignKey('form.id'), nullable=False)
    participant_id = db.Column(
        db.Integer, db.ForeignKey('participant.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'))
    data = db.Column(JSONB)
    submission_type = db.Column(ChoiceType(SUBMISSION_TYPES))
    created = db.Column(db.DateTime, default=current_timestamp)
    updated = db.Column(db.DateTime, onupdate=current_timestamp)
    sender_verified = db.Column(db.Boolean, default=True)
    deployment = db.relationship('Deployment', backref='submissions')
    event = db.relationship('Event', backref='submissions')
    form = db.relationship('Form', backref='submissions')
    location = db.relationship('Location', backref='submissions')
    participant = db.relationship('Participant', backref='submissions')


class SubmissionComment(BaseModel):
    __tablename__ = 'submission_comment'

    id = db.Column(
        db.Integer, db.Sequence('submmision_comment_id_seq'),
        primary_key=True)
    submission_id = db.Column(
        db.Integer, db.ForeignKey('submission.id'), nullable=False)
    submission = db.relationship('Submission', backref='comments')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='submission_comments')
    comment = db.Column(db.String)
    submit_date = db.Column(db.DateTime, default=current_timestamp)
    deployment_id = db.Column(
        db.Integer, db.ForeignKey('deployment.id'), nullable=False)
    deployment = db.relationship('Deployment', backref='submission_comments')


class SubmissionVersion(BaseModel):
    __tablename__ = 'submission_version'

    CHANNEL_CHOICES = (
        ('SMS', _('SMS')),
        ('WEB', _('Web')),
        ('API', _('API')),
        ('ODK', _('ODK')),
    )
    id = db.Column(
        db.Integer, db.Sequence('submmision_version_id_seq'),
        primary_key=True)
    submission_id = db.Column(
        db.Integer, db.ForeignKey('submission.id'), nullable=False)
    submission = db.relationship('Submission', backref='versions')
    timestamp = db.Column(db.DateTime, default=current_timestamp)
    channel = db.Column(ChoiceType(CHANNEL_CHOICES))
    deployment_id = db.Column(
        db.Integer, db.ForeignKey('deployment.id'), nullable=False)
    deployment = db.relationship('Deployment', backref='submission_versions')
    identity = db.Column(db.String, default='unknown', nullable=False)
