# -*- coding: utf-8 -*-
import re

from flask_babelex import get_locale, lazy_gettext as _
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy_i18n import make_translatable, translation_base, Translatable
import sqlalchemy_utils

from apollo import utils
from apollo.constants import LANGUAGES
from apollo.core import db
from apollo.dal.models import BaseModel, Resource

make_translatable(options={'locales': LANGUAGES.keys()})

number_cleaner = re.compile(r'[^0-9]+', re.I)
sqlalchemy_utils.i18n.get_locale = get_locale


class ParticipantSet(BaseModel):
    __tablename__ = 'participant_set'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    slug = db.Column(db.String)
    location_set_id = db.Column(
        db.Integer, db.ForeignKey('location_set.id', ondelete='CASCADE'),
        nullable=False)
    deployment_id = db.Column(
        db.Integer, db.ForeignKey('deployment.id', ondelete='CASCADE'),
        nullable=False)
    deployment = db.relationship(
        'Deployment',
        backref=db.backref(
            'participant_sets', cascade='all, delete', passive_deletes=True))
    location_set = db.relationship(
        'LocationSet',
        backref=db.backref(
            'participant_sets', cascade='all, delete', passive_deletes=True))

    def __str__(self):
        return self.name or ''

    def get_import_fields(self):
        fields = {
            'role': _('Role'),
            'sample': _('Sample'),
            'id': _('Participant ID'),
            'name': _('Name'),
            'supervisor': _('Supervisor'),
            'phone': _('Phone'),
            'partner': _('Partner'),
            'location': _('Location code'),
            'group': _('Group'),
            'gender': _('Gender'),
            'email': _('Email'),
            'password': _('Password')
        }

        extra_fields = ParticipantDataField.query.filter_by(
            participant_set_id=self.id).all()
        for ex_field in extra_fields:
            fields[ex_field.id] = ex_field.label

        return fields


class ParticipantDataField(Resource):
    __mapper_args__ = {'polymorphic_identity': 'participant_data_field'}
    __tablename__ = 'participant_data_field'

    id = db.Column(db.Integer, primary_key=True)
    participant_set_id = db.Column(
        db.Integer, db.ForeignKey('participant_set.id', ondelete='CASCADE'),
        nullable=False)
    name = db.Column(db.String, nullable=False)
    label = db.Column(db.String, nullable=False)
    visible_in_lists = db.Column(db.Boolean, default=False)
    resource_id = db.Column(
        db.Integer, db.ForeignKey('resource.resource_id', ondelete='CASCADE'))
    participant_set = db.relationship(
        'ParticipantSet',
        backref=db.backref(
            'extra_fields', cascade='all, delete', passive_deletes=True))

    def __str__(self):
        return str(
            _('ParticipantDataField - %(name)s in %(participant_set)s',
              name=self.name, participant_set=self.participant_set.name))


groups_participants = db.Table(
    'participant_groups_participants',
    db.Column('group_id', db.Integer,
              db.ForeignKey('participant_group.id', ondelete='CASCADE'),
              nullable=False),
    db.Column('participant_id', db.Integer,
              db.ForeignKey('participant.id', ondelete='CASCADE'),
              nullable=False)
)


class ParticipantRole(BaseModel):
    __tablename__ = 'participant_role'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    participant_set_id = db.Column(
        db.Integer, db.ForeignKey('participant_set.id', ondelete='CASCADE'),
        nullable=False)

    participant_set = db.relationship(
        'ParticipantSet',
        backref=db.backref(
            'participant_roles', cascade='all, delete', passive_deletes=True))

    def __str__(self):
        return self.name or ''


class ParticipantPartner(BaseModel):
    __tablename__ = 'participant_partner'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    participant_set_id = db.Column(db.Integer, db.ForeignKey(
        'participant_set.id', ondelete='CASCADE'), nullable=False)

    participant_set = db.relationship(
        'ParticipantSet',
        backref=db.backref('participant_partners', cascade='all, delete',
                           passive_deletes=True))

    def __str__(self):
        return self.name or ''


class ParticipantGroupType(BaseModel):
    __tablename__ = 'participant_group_type'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    participant_set_id = db.Column(db.Integer, db.ForeignKey(
        'participant_set.id', ondelete='CASCADE'), nullable=False)

    participant_set = db.relationship(
        'ParticipantSet', backref=db.backref(
            'participant_group_types', cascade='all, delete'))

    def __str__(self):
        return self.name or ''


class ParticipantGroup(BaseModel):
    __tablename__ = 'participant_group'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    group_type_id = db.Column(db.Integer, db.ForeignKey(
        'participant_group_type.id', ondelete='CASCADE'), nullable=False)
    participant_set_id = db.Column(
        db.Integer, db.ForeignKey('participant_set.id', ondelete='CASCADE'),
        nullable=False)

    group_type = db.relationship(
        'ParticipantGroupType',
        backref=db.backref('participant_groups', cascade='all, delete'))
    participant_set = db.relationship(
        'ParticipantSet',
        backref=db.backref('participant_groups', cascade='all, delete'))

    def __str__(self):
        return self.name or ''


class Phone(BaseModel):
    __tablename__ = 'phone'
    __table_args__ = (
        db.UniqueConstraint('number'),
    )

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String, nullable=False)

    def __init__(self, number):
        self.number = number_cleaner.sub('', number)


class Participant(Translatable, BaseModel):
    GENDER = (
        ('', _('Unspecified')),
        ('F', _('Female')),
        ('M', _('Male')),
    )

    __tablename__ = 'participant'
    __translatable__ = {'locales': LANGUAGES.keys()}

    locale = 'en'   # default locale

    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.String)
    role_id = db.Column(db.Integer, db.ForeignKey(
        'participant_role.id', ondelete='SET NULL'))
    partner_id = db.Column(db.Integer, db.ForeignKey(
        'participant_partner.id', ondelete='SET NULL'))
    supervisor_id = db.Column(db.Integer, db.ForeignKey(
        'participant.id', ondelete='SET NULL'))
    gender = db.Column(sqlalchemy_utils.ChoiceType(GENDER))
    email = db.Column(db.String)
    location_id = db.Column(
        db.Integer, db.ForeignKey('location.id', ondelete='CASCADE'))
    participant_set_id = db.Column(db.Integer, db.ForeignKey(
        'participant_set.id', ondelete='CASCADE'), nullable=False)
    message_count = db.Column(db.Integer, default=0)
    accurate_message_count = db.Column(db.Integer, default=0)
    completion_rating = db.Column(db.Float, default=1)
    device_id = db.Column(db.String)
    password = db.Column(db.String)
    extra_data = db.Column(JSONB)

    location = db.relationship('Location', backref='participants')
    participant_set = db.relationship(
        'ParticipantSet', backref=db.backref(
            'participants', cascade='all, delete', lazy='dynamic',
            passive_deletes=True))
    groups = db.relationship(
        'ParticipantGroup', secondary=groups_participants,
        backref='participants')
    role = db.relationship('ParticipantRole', backref='participants')
    partner = db.relationship('ParticipantPartner', backref='participants')
    participant_phones = db.relationship(
        'ParticipantPhone',
        backref=db.backref('participants', cascade='all, delete'))
    supervisor = db.relationship('Participant', remote_side=id)

    def __str__(self):
        return self.name or ''

    @property
    def primary_phone(self):
        if not self.id:
            return None

        p_phone = ParticipantPhone.query.filter_by(
            participant_id=self.id).order_by(
                ParticipantPhone.phone_id).first()

        return p_phone.phone.number if p_phone else None

    @property
    def phones(self):
        if not self.id:
            return None

        if not hasattr(self, '_phones'):
            phones = Phone.query.join(
                ParticipantPhone,
                Phone.id == ParticipantPhone.phone_id
            ).filter(
                ParticipantPhone.participant_id == self.id
            ).order_by(ParticipantPhone.last_seen).all()
            self._phones = phones

        return self._phones

    @property
    def gender_display(self):
        if not self.gender:
            return Participant.GENDER[0][1]

        d = dict(Participant.GENDER)
        return d.get(self.gender, Participant.GENDER[0][1])


class ParticipantTranslation(translation_base(Participant)):
    __tablename__ = 'participant_translation'

    name = db.Column(db.Unicode(255))


class ParticipantPhone(BaseModel):
    __tablename__ = 'participant_phone'

    participant_id = db.Column(
        db.Integer, db.ForeignKey('participant.id', ondelete='CASCADE'),
        primary_key=True)
    phone_id = db.Column(
        db.Integer, db.ForeignKey('phone.id', ondelete='CASCADE'),
        primary_key=True)
    last_seen = db.Column(db.DateTime, default=utils.current_timestamp)
    verified = db.Column(db.Boolean, default=True)
    phone = db.relationship('Phone')
