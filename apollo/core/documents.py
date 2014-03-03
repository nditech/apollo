from mongoengine import *


# Deployments
class Deployment(Document):
    '''Multi-tenancy in Apollo is managed using a system of deployments.
    Each deployment is separated from the other based on hostnames supplied
    by a browser or requesting agent.

    :attr:`name` A name given to the deployment.
    :attr:`database` The name of the database where all collections for
    the deployment will be stored.
    :attr:`hostnames` A list of hostnames representing the deployment.'''

    name = StringField()
    hostnames = ListField(StringField())

    meta = {
        'indexes': [
            ['hostnames']
        ]
    }

    def __unicode__(self):
        return self.name


# Event
class Event(Document):
    deployment = ReferenceField('Deployment')
    name = StringField()
    start_date = DateTimeField()
    end_date = DateTimeField()

    meta = {
        'indexes': [
            ['deployment', 'name'],
            ['deployment', 'start_date', '-end_date']
        ]
    }

    def __unicode__(self):
        return self.name


# Forms
class FormField(EmbeddedDocument):
    '''A :class:`mongoengine.EmbeddedDocument` used in storing the
    Checklist/Critical Incident form questions in a :class:`core.models.Form`
    model.

    Each :class:`core.models.FormField` has attributes for specifying various
    behaviour for the form field.

    :attr:`analysis_type` which specifies the sort of data analysis to be
    performed on the field and is defined by the values stored
    in :attr:`ANALYSIS_TYPES`

    :attr:`represents_boolean` which is either True for a FormField that
    accepts only one value (e.g. Critical Incident form fields)

    :attr:`options` which is a dictionary that has keys representing
    field option values and values representing the option description.
    (e.g. {'1': 'Yes'})

    :attr:`allows_multiple_values` which is a boolean field specifying whether
    the field will accept multiple values as correct responses

    :attr:`min_value` which specifies the minimum accepted value and
    :attr:`max_value` for specifying the maximum valid value.

    :attr:`description` stores the textual description of the field.

    :attr:`name` is the question code used to identify the field (e.g. AA)'''

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
    '''The :class:`core.models.FormGroup` model provides storage for form
    groups in a :class:`core.models.Form` and are the organizational structure
    for form fields. Besides the :attr:`fields` attribute for storing
    form fields, there's also a :attr:`name` attribute for storing the name.'''

    name = StringField(required=True)
    fields = ListField(EmbeddedDocumentField('FormField'))


class Form(Document):
    '''Primary storage for Checklist/Incident Forms.
    Defines the following attributes:

    :attr:`events` a list of refernces to :class:`core.models.Event` objects
    defining which events this form is to be used in.

    :attr:`groups` storage for the form groups in the form.

    :attr:`form_type` for specifying the type of the form as described
    by :attr:`FORM_TYPES`.

    :attr:`prefix` determines the prefix for the form. This prefix is used in
    identifying which form is to be used in parsing incoming submissions.

    :attr:`name` is the name for this form.'''

    FORM_TYPES = (
        ('CHECKLIST', 'Checklist Form'),
        ('INCIDENT', 'Incident Form'))

    name = StringField(required=True)
    prefix = StringField()
    form_type = StringField(choices=FORM_TYPES)
    groups = ListField(EmbeddedDocumentField('FormGroup'))
    events = ListField(ReferenceField('Event'))

    meta = {
        'indexes': [
            ['prefix'],
            ['events'],
            ['events', 'prefix'],
            ['events', 'form_type']
        ]
    }

    def __unicode__(self):
        return self.name


# Submissions
class Submission(DynamicEmbeddedDocument):
    '''Submissions represent data collected by participants in response to
    questions in Checklist and Critical Incident forms. Submissions are created
    prior to data input and are updated whenever data is received. The only
    exception is for the storage of Critical Incident reports which create
    submissions when data input is received.

    The :class:`core.models.Submission` model
    is a :class:`mongoengine.DynamicEmbeddedDocument` and hence, most of it's
    functionality isn't stored within the model and gets defined at run time
    depending on the configuration of forms, form groups and form fields.

    :attr:`updated` is a :class:`mongoengine.DateTimeField` that stores the
    last time the submission was updated.

    :attr:`created` is a :class:`mongoengine.DateTimeField` that stores the
    date of creation for the submission.

    :attr:`contributor` stores the contributing participant for
    this submission.

    :attr:`form` provides a reference to the form that the submission was
    made for.
    '''

    form = ReferenceField('Form')
    contributor = ReferenceField('Participant')
    created = DateTimeField()
    updated = DateTimeField()


# Locations
class Sample(Document):
    '''Samples allow for the storage of groups of Locations that can be used
    to create samples for analysis or data management.'''

    name = StringField()
    events = ListField(ReferenceField('Event'))

    meta = {
        'indexes': [
            ['events']
        ]
    }


class LocationTypeAncestor(EmbeddedDocument):
    '''An embedded document used by the :class:`core.models.LocationType`
    model for storing denormalized ancestry data'''

    name = StringField()


class LocationType(Document):
    '''Stores the type describing the administrative level of a Location
    :param ancestors: This stores a list references to ancestor
    loction types as documented in
    http://docs.mongodb.org/manual/tutorial/model-tree-structures/'''

    name = StringField()
    ancestors_ref = ListField(ReferenceField('LocationType'))
    on_submissions_view = BooleanField(default=False)
    on_dashboard_view = BooleanField(default=False)
    on_analysis_view = BooleanField(default=False)
    events = ListField(ReferenceField('Event'))

    meta = {
        'indexes': [
            ['events']
        ]
    }

    @classmethod
    def get_root_for_event(cls, event):
        return cls.objects.get(events=event, __raw__={'ancestors_ref': []})

    def get_children(self):
        tree = [node.id for node in self.ancestors_ref]
        tree.append(self.id)
        return LocationType.objects(__raw__={'ancestors_ref': tree})

    def __unicode__(self):
        return self.name


class LocationAncestor(EmbeddedDocument):
    '''An embedded document for storing location ancestors data to enable
    fast retrieval of data fields'''
    name = StringField()
    location_type = StringField()


class Location(Document):
    '''A store for Locations'''

    name = StringField()
    code = StringField()
    location_type = StringField()
    coords = GeoPointField()
    ancestors_ref = ListField(ReferenceField('Location'))
    ancestors = ListField(EmbeddedDocumentField('LocationAncestor'))
    samples = ListField(ReferenceField('Sample'))
    submissions = ListField(EmbeddedDocumentField('Submission'))
    events = ListField(ReferenceField('Event'))

    meta = {
        'indexes': [
            ['ancestors_ref'],
            ['ancestors_ref', 'location_type'],
            ['samples'],
            ['events'],
            ['location_type'],
            ['name', 'location_type'],
            ['code'],
            ['events', 'code']
        ]
    }

    @classmethod
    def get_root_for_event(cls, event):
        return cls.objects.get(events=event, __raw__={'ancestors_ref': []})

    def get_children(self):
        tree = [node.id for node in self.ancestors_ref]
        tree.append(self.id)
        return Location.objects(__raw__={'ancestors_ref': tree})

    def __unicode__(self):
        return self.name


# Participants
class ParticipantRole(Document):
    '''Stores the role for a participant. (e.g. Supervisor, Co-ordinator)'''

    name = StringField()

    def __unicode__(self):
        return self.name


class ParticipantPartner(Document):
    '''Storage for the participant partner organization'''

    name = StringField()

    def __unicode__(self):
        return self.name


class Participant(DynamicDocument):
    '''Storage for participant contact information'''

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
    events = ListField(ReferenceField('Event'))

    def __unicode__(self):
        return self.name
