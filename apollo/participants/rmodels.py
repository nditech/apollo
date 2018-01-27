# -*- coding: utf-8 -*-
from babel import lazy_gettext as _
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy_utils import ChoiceType

from apollo.core import db2
from apollo.dal.models import BaseModel


class ParticipantRole(BaseModel):
    __tablename__ = 'participant_roles'

    id = db2.Column(
        db2.Integer, db2.Sequence('participant_role_id_seq'), primary_key=True)
    name = db2.Column(db2.String)
    deployment_id = db2.Column(db2.Integer, db2.ForeignKey('deployments.id'))

    deployment = db2.relationship(
        'Deployment', back_populates='participant_roles')

    def __str__(self):
        return self.name or ''


class ParticipantPartner(BaseModel):
    __tablename__ = 'participant_partners'

    id = db2.Column(
        db2.Integer, db2.Sequence('participant_partner_id_seq'),
        primary_key=True)
    name = db2.Column(db2.String)
    deployment_id = db2.Column(db2.Integer, db2.ForeignKey('deployments.id'))

    deployment = db2.relationship(
        'Deployment', back_populates='participant_partners')

    def __str__(self):
        return self.name or ''


class ParticipantGroupType(BaseModel):
    __tablename__ = 'participant_group_types'

    id = db2.Column(
        db2.Integer, db2.Sequence('participant_group_type_id_seq'),
        primary_key=True)
    name = db2.Column(db2.String)
    deployment_id = db2.Column(db2.Integer, db2.ForeignKey('deployments.id'))

    deployment = db2.relationship(
        'Deployment', back_populates='participant_group_types')

    def __str__(self):
        return self.name or ''


class ParticipantGroup(BaseModel):
    __tablename__ = 'participant_groups'

    id = db2.Column(
        db2.Integer, db2.Sequence('participant_group_id_seq'),
        primary_key=True)
    name = db2.Column(db2.String)
    deployment_id = db2.Column(db2.Integer, db2.ForeignKey('deployments.id'))
    group_type_id = db2.Column(
        db2.Integer, db2.ForeignKey('participant_group_types.id'))

    deployment = db2.relationship(
        'Deployment', back_populates='participant_groups')
    group_type = db2.relationship(
        'ParticipantGroupType', back_populates='participant_groups')

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

    __tablename__ = 'participants'
    id = db2.Column(
        db2.Integer, db2.Sequence('participant_id_seq'), primary_key=True)
    name = db2.Column(db2.String)
    role_id = db2.Column(
        db2.Integer, db2.ForeignKey('participant_roles.id'))
    partner_id = db2.Column(
        db2.Integer, db2.ForeignKey('participant_partners.id'))
    supervisor_id = db2.Column(
        db2.Integer, db2.ForeignKey('participants.id'))
    gender = ChoiceType(GENDER, default=0)
    email = db2.Column(db2.String)
    deployment_id = db2.Column(db2.Integer, db2.ForeignKey('deployments.id'))
    message_count = db2.Column(db2.Integer, default=0)
    accurate_message_count = db2.Column(db2.Integer, default=0)
    completion_rating = db2.Column(db2.Float, default=1)
    device_id = db2.Column(db2.String)
    password = db2.Column(db2.String)
    phones = db2.Column(JSONB)

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
