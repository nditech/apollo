# -*- coding: utf-8 -*-
from flask_babelex import lazy_gettext as _
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy_utils import ChoiceType

from apollo.core import db
from apollo.dal.models import BaseModel


class ParticipantRole(BaseModel):
    __tablename__ = 'participant_role'

    id = db.Column(
        db.Integer, db.Sequence('participant_role_id_seq'), primary_key=True)
    name = db.Column(db.String, nullable=False)
    deployment_id = db.Column(db.Integer, db.ForeignKey(
        'deployment.id', ondelete='CASCADE'), nullable=False)
    participant_set_id = db.Column(
        db.Integer, db.ForeignKey('participant_set.id'), nullable=False)

    deployment = db.relationship(
        'Deployment', backref='participant_roles')
    participant_set = db.relationship(
        'ParticipantSet', backref='participant_roles')

    def __str__(self):
        return self.name or ''


class ParticipantPartner(BaseModel):
    __tablename__ = 'participant_partner'

    id = db.Column(
        db.Integer, db.Sequence('participant_partner_id_seq'),
        primary_key=True)
    name = db.Column(db.String, nullable=False)
    deployment_id = db.Column(db.Integer, db.ForeignKey(
         'deployment.id', ondelete='CASCADE'), nullable=False)
    participant_set_id = db.Column(db.Integer, db.ForeignKey(
        'participant_set.id', ondelete='CASCADE'), nullable=False)

    deployment = db.relationship(
        'Deployment', backref='participant_partners')
    participant_set = db.relationship(
        'ParticipantSet', backref='participant_partners')

    def __str__(self):
        return self.name or ''


class ParticipantGroupType(BaseModel):
    __tablename__ = 'participant_group_type'

    id = db.Column(
        db.Integer, db.Sequence('participant_group_type_id_seq'),
        primary_key=True)
    name = db.Column(db.String)
    deployment_id = db.Column(db.Integer, db.ForeignKey(
        'deployment.id', ondelete='CASCADE'), nullable=False)
    participant_set_id = db.Column(db.Integer, db.ForeignKey(
        'participant_set.id', ondelete='CASCADE'), nullable=False)

    deployment = db.relationship(
        'Deployment', backref='participant_group_types')
    participant_set = db.relationship(
        'ParticipantSet', backref='participant_group_types')

    def __str__(self):
        return self.name or ''


class ParticipantGroup(BaseModel):
    __tablename__ = 'participant_group'

    id = db.Column(
        db.Integer, db.Sequence('participant_group_id_seq'),
        primary_key=True)
    name = db.Column(db.String, nullable=False)
    deployment_id = db.Column(db.Integer, db.ForeignKey(
        'deployment.id', ondelete='CASCADE'), nullable=False)
    group_type_id = db.Column(db.Integer, db.ForeignKey(
        'participant_group_type.id', ondelete='CASCADE'), nullable=False)

    deployment = db.relationship(
        'Deployment', backref='participant_groups')
    group_type = db.relationship(
        'ParticipantGroupType', backref='participant_groups')

    def __str__(self):
        return self.name or ''


class Participant(BaseModel):
    '''
    The *proposed* structure of the phones list is as below:
        {
            'number': <string>,
            'last_seen': <datetime>,
            'verified': <boolean>,
            'is_primary': <boolean>
        }
    '''
    GENDER = (
        (0, _('Unspecified')),
        (1, _('Female')),
        (2, _('Male')),
    )

    __tablename__ = 'participant'
    id = db.Column(
        db.Integer, db.Sequence('participant_id_seq'), primary_key=True)
    name = db.Column(db.String)
    role_id = db.Column(db.Integer, db.ForeignKey(
        'participant_role.id', ondelete='SET NULL'))
    partner_id = db.Column(db.Integer, db.ForeignKey(
        'participant_partner.id', ondelete='SET NULL'))
    supervisor_id = db.Column(db.Integer, db.ForeignKey(
        'participant.id', ondelete='SET NULL'))
    gender = db.Column(ChoiceType(GENDER), default=0)
    email = db.Column(db.String)
    deployment_id = db.Column(db.Integer, db.ForeignKey(
        'deployment.id', ondelete='CASCADE'), nullable=False)
    participant_set_id = db.Column(db.Integer, db.ForeignKey(
        'participant_set.id', ondelete='CASCADE'), nullable=False)
    message_count = db.Column(db.Integer, default=0)
    accurate_message_count = db.Column(db.Integer, default=0)
    completion_rating = db.Column(db.Float, default=1)
    device_id = db.Column(db.String)
    password = db.Column(db.String)
    phones = db.Column(JSONB)

    deployment = db.relationship('Deployment', backref='participants')
    participant_set = db.relationship(
        'ParticipantSet', backref='participants')

    def __str__(self):
        return self.name or ''

    @property
    def primary_phone(self):
        try:
            return next(
                p.get('number') for p in self.phones
                if p.get('is_primary', False)
            )
        except StopIteration:
            return None
