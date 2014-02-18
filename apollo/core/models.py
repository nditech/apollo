from mongoengine import *


# Event
class Event(Document):
    name = StringField()
    state_date = DateTimeField()
    end_date = DateTimeField()


# Forms
class FormField(EmbeddedDocument):
    '''FormFields are used in storing the questions in a Form'''

    ANALYSIS_TYPES = (
        ('N/A', 'Not Applicable'),
        ('PROCESS', 'Process Analysis'),
        ('RESULT', 'Results Analysis'))

    name = StringField(required=True)
    description = StringField(required=True)
    max_value = IntField(default=9999)
    min_value = IntField(default=0)
    allows_multiple_values = BooleanField(default=False)
    options = DictField()
    represents_boolean = BooleanField(default=False)
    analysis_type = StringField(choices=ANALYSIS_TYPES, default='N/A')


class FormGroup(EmbeddedDocument):
    '''Each Form has a number of FormGroups for categorizing FormFields'''

    name = StringField(required=True)
    fields = ListField(EmbeddedDocumentField('FormField'))


class Form(Document):
    '''Storage for Checklist/Incident Forms'''

    FORM_TYPES = (
        ('CHECKLIST', 'Checklist Form'),
        ('INCIDENT', 'Incident Form'))

    name = StringField(required=True)
    prefix = StringField()
    form_type = StringField(choices=FORM_TYPES)
    groups = ListField(EmbeddedDocumentField('FormGroup'))
    events = ListField(ReferenceField('Event'))


# Submissions
class Submission(EmbeddedDocument):
    '''Submissions are where Form data is stored'''

    form = ReferenceField('Form')
    contributor = ReferenceField('Participant')
    data = DictField()
    created = DateTimeField()
    updated = DateTimeField()


# Locations
class LocationType(Document):
    '''Stores the type describing the administrative level of a Location
    :param ancestors: This stores a list references to ancestor
    loction types as documented in
    http://docs.mongodb.org/manual/tutorial/model-tree-structures/'''

    name = StringField()
    ancestors = ListField(ReferenceField('LocationType'))


class Location(Document):
    '''A store for Locations'''

    code = StringField()
    location_type = ReferenceField('LocationType')
    coords = GeoPointField()
    ancestors = ListField(ReferenceField('Location'))
    submissions = ListField(EmbeddedDocumentField('Submission'))


# Participants
class ParticipantRole(Document):
    name = StringField()


class ParticipantPartner(Document):
    name = StringField()


class Participant(DynamicDocument):
    GENDER = (
        ('F', 'Female'),
        ('M', 'Male'))
    participant_id = StringField()
    name = StringField()
    role = ReferenceField('ParticipantRole')
    partner = ReferenceField('ParticipantPartner')
    location = ReferenceField('Location')
    supervisor = ReferenceField('Participant')
    gender = StringField(choices=GENDER)
