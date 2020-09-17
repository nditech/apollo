# -*- coding: utf-8 -*-
from itertools import chain
import re

from sqlalchemy import func
from flask_babelex import lazy_gettext as _
from sqlalchemy.dialects.postgresql import JSONB
import sqlalchemy_utils

from apollo import utils
from apollo.core import db
from apollo.dal.models import BaseModel, Resource, translation_hybrid


number_cleaner = re.compile(r'[^0-9]+', re.I)


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
    gender_hidden = db.Column(db.Boolean, default=False)
    role_hidden = db.Column(db.Boolean, default=False)
    partner_hidden = db.Column(db.Boolean, default=False)

    def __str__(self):
        return self.name or ''

    def get_import_fields(self):
        fields = {
            'role': _('Role'),
            'sample': _('Sample'),
            'id': _('Participant ID'),
            'supervisor': _('Supervisor ID'),
            'phone': _('Phone'),
            'partner': _('Partner'),
            'location': _('Location code'),
            'group': _('Group'),
            'gender': _('Gender'),
            'email': _('Email'),
            'password': _('Password')
        }
        for locale, language in self.deployment.languages.items():
            fields[f'full_name_{locale}'] = _(
                'Full Name (%(language)s)', language=language)
        for locale, language in self.deployment.languages.items():
            fields[f'first_name_{locale}'] = _(
                'First Name (%(language)s)', language=language)
        for locale, language in self.deployment.languages.items():
            fields[f'other_names_{locale}'] = _(
                'Other Names (%(language)s)', language=language)
        for locale, language in self.deployment.languages.items():
            fields[f'last_name_{locale}'] = _(
                'Last Name (%(language)s)', language=language)

        extra_fields = ParticipantDataField.query.filter_by(
            participant_set_id=self.id).all()
        for ex_field in extra_fields:
            fields[ex_field.id] = ex_field.label

        return fields


samples_participants = db.Table(
    "samples_participants",
    db.Column(
        "sample_id",
        db.Integer,
        db.ForeignKey("sample.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    ),
    db.Column(
        "participant_id",
        db.Integer,
        db.ForeignKey("participant.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    ),
)


class Sample(BaseModel):
    __tablename__ = "sample"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    participant_set_id = db.Column(
        db.Integer,
        db.ForeignKey("participant_set.id", ondelete="CASCADE"),
        nullable=False
    )

    participant_set = db.relationship(
        "ParticipantSet",
        backref=db.backref(
            "samples", cascade="all, delete", lazy="dynamic",
            passive_deletes=True)
    )


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
            'extra_fields', cascade='all, delete-orphan',
            passive_deletes=True))

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


class Participant(BaseModel):
    GENDER = (
        ('', _('Unspecified')),
        ('F', _('Female')),
        ('M', _('Male')),
    )

    __tablename__ = 'participant'

    id = db.Column(db.Integer, primary_key=True)
    full_name_translations = db.Column(JSONB)
    first_name_translations = db.Column(JSONB)
    other_names_translations = db.Column(JSONB)
    last_name_translations = db.Column(JSONB)
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

    full_name = translation_hybrid(full_name_translations)
    first_name = translation_hybrid(first_name_translations)
    other_names = translation_hybrid(other_names_translations)
    last_name = translation_hybrid(last_name_translations)

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
    phone_contacts = db.relationship(
        'PhoneContact',
        backref=db.backref('participants', cascade='all, delete'))
    supervisor = db.relationship('Participant', remote_side=id)
    samples = db.relationship(
        "Sample",
        backref="participants",
        secondary=samples_participants,
    )

    def __str__(self):
        return self.name or ''

    @property
    def primary_phone(self):
        if not self.id:
            return None

        p_phone = PhoneContact.query.filter_by(
            participant_id=self.id, verified=True).order_by(
                PhoneContact.updated.desc()).first()

        return p_phone.number if p_phone else None

    @property
    def other_phones(self):
        if not self.id:
            return None

        phone_primary = PhoneContact.query.filter_by(
            participant_id=self.id, verified=True).order_by(
                PhoneContact.updated.desc()).first()

        if phone_primary:
            other_phones = PhoneContact.query.filter(
                PhoneContact.participant_id==self.id,  # noqa
                PhoneContact.id!=phone_primary.id,  # noqa
                PhoneContact.verified==True  # noqa
            ).order_by(
                PhoneContact.updated.desc()
            ).with_entities(
                PhoneContact.number
            ).all()

            return list(chain(*other_phones))

        return []

    @property
    def phones(self):
        if not self.id:
            return None

        if not hasattr(self, '_phones'):
            phones = PhoneContact.query.filter_by(
                participant_id=self.id
            ).order_by(
                PhoneContact.verified.desc(),
                PhoneContact.updated.desc()).all()
            self._phones = phones

        return self._phones

    @property
    def gender_display(self):
        if not self.gender:
            return Participant.GENDER[0][1]

        d = dict(Participant.GENDER)
        return d.get(self.gender, Participant.GENDER[0][1])

    @property
    def last_contacted(self):
        contact = ContactHistory.query.filter(
            ContactHistory.participant == self
        ).order_by(ContactHistory.created.desc()).first()

        if contact:
            return contact.created
        else:
            return None

    @property
    def name(self):
        if self.full_name:
            return self.full_name

        names = [self.first_name, self.other_names, self.last_name]
        names = [n for n in names if n]

        return ' '.join(names)


ParticipantFullNameTranslations = func.jsonb_each_text(
    Participant.full_name_translations).alias('translations')
ParticipantFirstNameTranslations = func.jsonb_each_text(
    Participant.first_name_translations).alias('first_name_translations')
ParticipantOtherNamesTranslations = func.jsonb_each_text(
    Participant.other_names_translations).alias('other_names_translations')
ParticipantLastNameTranslations = func.jsonb_each_text(
    Participant.last_name_translations).alias('last_translations')


class PhoneContact(BaseModel):
    __tablename__ = 'phone_contact'

    id = db.Column(db.Integer, nullable=False, primary_key=True)
    participant_id = db.Column(
        db.Integer, db.ForeignKey('participant.id', ondelete='CASCADE'),
        nullable=False)
    number = db.Column(db.String, nullable=False)
    created = db.Column(
        db.DateTime, nullable=False, default=utils.current_timestamp)
    updated = db.Column(
        db.DateTime, nullable=False, default=utils.current_timestamp,
        onupdate=utils.current_timestamp)
    verified = db.Column(db.Boolean, default=False)

    participant = db.relationship('Participant')

    def touch(self):
        self.updated = utils.current_timestamp()


class ContactHistory(BaseModel):
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    participant_id = db.Column(
        db.Integer, db.ForeignKey('participant.id', ondelete='CASCADE'),
        nullable=False)
    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False)
    description = db.Column(db.String)
    created = db.Column(
        db.DateTime, nullable=False, default=utils.current_timestamp)

    participant = db.relationship(
        'Participant',
        backref=db.backref('contact_history', cascade='all, delete',
                           passive_deletes=True))
    user = db.relationship(
        'User',
        backref=db.backref('contact_history', cascade='all, delete',
                           passive_deletes=True))
