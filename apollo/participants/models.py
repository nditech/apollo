from ..core import db
from ..deployments.models import Deployment, Event


# Participants
class ParticipantRole(db.Document):
    '''Stores the role for a participant. (e.g. Supervisor, Co-ordinator)'''

    name = db.StringField()

    deployment = db.ReferenceField(Deployment)

    def __unicode__(self):
        return self.name


class ParticipantPartner(db.Document):
    '''Storage for the participant partner organization'''

    name = db.StringField()

    deployment = db.ReferenceField(Deployment)

    def __unicode__(self):
        return self.name


class PhoneContact(db.EmbeddedDocument):
    number = db.StringField()
    verified = db.BooleanField(default=False)


class Participant(db.DynamicDocument):
    '''Storage for participant contact information'''

    GENDER = (
        ('F', 'Female'),
        ('M', 'Male'))
    participant_id = db.StringField()
    name = db.StringField()
    role = db.ReferenceField('ParticipantRole')
    partner = db.ReferenceField('ParticipantPartner')
    location = db.ReferenceField('Location')
    supervisor = db.ReferenceField('Participant')
    gender = db.StringField(choices=GENDER)

    email = db.EmailField()
    phones = db.ListField(db.EmbeddedDocumentField(PhoneContact))

    events = db.ListField(db.ReferenceField('Event'))
    deployment = db.ReferenceField(Deployment)

    def __unicode__(self):
        return self.name
