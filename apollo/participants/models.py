from datetime import datetime
from flask.ext.babel import lazy_gettext as _
from flask.ext.mongoengine import BaseQuerySet
from mongoengine import Q
from apollo.core import db
from apollo.deployments.models import Deployment, Event
from apollo.helpers import compute_location_path


class ParticipantQuerySet(BaseQuerySet):
    def filter_in(self, location):
        param = 'location_name_path__{}'.format(location.location_type)
        query_kwargs = {
            param: location.name
        }
        return self(Q(location=location) | Q(**query_kwargs))


# Participants
class ParticipantRole(db.Document):
    '''Stores the role for a participant. (e.g. Supervisor, Co-ordinator)'''

    name = db.StringField()

    deployment = db.ReferenceField(Deployment)

    def __unicode__(self):
        return self.name or u''


class ParticipantPartner(db.Document):
    '''Storage for the participant partner organization'''

    name = db.StringField()

    deployment = db.ReferenceField(Deployment)

    def __unicode__(self):
        return self.name or u''


class ParticipantGroupType(db.Document):
    name = db.StringField()
    deployment = db.ReferenceField(Deployment)

    def __unicode__(self):
        return self.name or u''


class ParticipantGroup(db.Document):
    name = db.StringField()
    deployment = db.ReferenceField(Deployment)
    group_type = db.StringField()

    def __unicode__(self):
        return self.name or u''


class PhoneContact(db.EmbeddedDocument):
    number = db.StringField()
    verified = db.BooleanField(default=False)
    last_seen = db.DateTimeField()

    def __unicode__(self):
        return self.number or u''


class Participant(db.DynamicDocument):
    '''Storage for participant contact information'''

    GENDER = (
        ('F', _('Female')),
        ('M', _('Male')),
        ('', _('Unspecified'))
    )

    participant_id = db.StringField()
    name = db.StringField()
    role = db.ReferenceField('ParticipantRole')
    partner = db.ReferenceField('ParticipantPartner')
    location = db.ReferenceField('Location')
    location_name_path = db.DictField()
    supervisor = db.ReferenceField('Participant')
    gender = db.StringField(choices=GENDER, default='')
    groups = db.ListField(db.ReferenceField(
        ParticipantGroup, reverse_delete_rule=db.PULL))

    email = db.EmailField()
    phones = db.ListField(db.EmbeddedDocumentField(PhoneContact))
    message_count = db.IntField(default=0)
    accurate_message_count = db.IntField(default=0)

    event = db.ReferenceField(Event)
    deployment = db.ReferenceField(Deployment)

    completion_rating = db.FloatField(default=1)
    device_id = db.StringField()
    password = db.StringField()

    meta = {
        'indexes': [
            ['participant_id'],
            ['device_id'],
            ['location'],
            ['phones.number'],
            ['event'],
            ['name'],
            ['role'],
            ['partner'],
            ['groups'],
            ['deployment'],
            ['deployment', 'event']
        ],
        'queryset_class': ParticipantQuerySet
    }

    def __unicode__(self):
        return self.name or u''

    def clean(self):
        # unlike for submissions, this always gets called, because
        # participants are 'mobile' - they can be moved from one location
        # to another. we want this to reflect that.
        self.location_name_path = compute_location_path(self.location)
        if self.gender not in map(lambda op: op[0], self.GENDER):
            self.gender = ''

    def get_phone(self):
        if self.phones:
            return self.phones[0].number
        else:
            return None

    def set_phone(self, value):
        # TODO: blind overwrite is silly. find a way to ensure the number
        # doesn't already exist
        if not self.phones:
            self.phones.append(PhoneContact(number=value, verified=True))
        else:
            self.phones[0].number = value
            self.phones[0].verified = True
        self.save()
        self.reload()

    phone = property(get_phone, set_phone)

    @property
    def last_seen_phone(self):
        if self.phones:
            phones = sorted(
                self.phones, key=lambda p: p.last_seen if p.last_seen
                else datetime.fromtimestamp(0))
            phones.reverse()
            return phones[0].number
        else:
            return None
