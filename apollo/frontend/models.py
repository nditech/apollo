from __future__ import absolute_import
from __future__ import unicode_literals
from apollo.application import db
from apollo.core.querysets import LocationQuerySet, SubmissionQuerySet
from datetime import datetime, timedelta
from slugify import slugify_unicode
from flask.ext.security import MongoEngineUserDatastore, RoleMixin, UserMixin


class Deployment(db.Document):
    name = db.StringField(required=True)
    hostnames = db.ListField(db.StringField())

    meta = {
        'indexes': [
            ['hostnames']
        ]
    }

    def __unicode__(self):
        return self.name


class Role(db.Document, RoleMixin):
    name = db.StringField(unique=True)
    description = db.StringField()
    deployment = db.ReferenceField(Deployment)


class User(db.Document, UserMixin):
    deployment = db.ReferenceField(Deployment)
    email = db.EmailField()
    password = db.StringField(max_length=255)
    active = db.BooleanField(default=True)
    confirnmed_at = db.DateTimeField()
    roles = db.ListField(db.ReferenceField(Role), default=[])

user_datastore = MongoEngineUserDatastore(db, User, Role)


# Event
class Event(db.Document):
    deployment = db.ReferenceField(Deployment)
    name = db.StringField()
    start_date = db.DateTimeField()
    end_date = db.DateTimeField()

    meta = {
        'indexes': [
            ['deployment', 'name'],
            ['deployment', 'start_date', '-end_date']
        ]
    }

    @classmethod
    def default(cls):
        current_timestamp = datetime.utcnow()
        ct = datetime(
            year=current_timestamp.year,
            month=current_timestamp.month,
            day=current_timestamp.day
        )

        lower_bound = ct - timedelta(hours=23)
        upper_bound = ct + timedelta(hours=23)

        event = cls.objects(
            start_date__lte=lower_bound, end_date__gte=upper_bound
        ).order_by('-start_date').first()
        if event:
            return event

        event = cls.objects(
            end_date__lte=lower_bound
        ).order_by('-end_date').first()
        if event:
            return event

        event = cls.objects(
            start_date__gte=upper_bound
        ).order_by('start_date').first()
        if event:
            return event
        return None

    def __unicode__(self):
        return self.name


# Forms
class FormField(db.EmbeddedDocument):
    '''A :class:`mongoengine.EmbeddedDocument` used in storing the
    Checklist/Critical Incident form questions in a
    :class:`core.documents.Form` model.

    Each :class:`core.documents.FormField` has attributes for specifying
    various behaviour for the form field.

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

    name = db.StringField(required=True)
    description = db.StringField(required=True)
    max_value = db.IntField(default=9999)
    min_value = db.IntField(default=0)
    allows_multiple_values = db.BooleanField(default=False)
    options = db.DictField()
    represents_boolean = db.BooleanField(default=False)
    analysis_type = db.StringField(choices=ANALYSIS_TYPES, default='N/A')


class FormGroup(db.EmbeddedDocument):
    '''The :class:`core.documents.FormGroup` model provides storage for form
    groups in a :class:`core.documents.Form` and are the organizational
    structure for form fields. Besides the :attr:`fields` attribute for storing
    form fields, there's also a :attr:`name` attribute for storing the name.'''

    name = db.StringField(required=True)
    slug = db.StringField(required=True)
    fields = db.ListField(db.EmbeddedDocumentField('FormField'))


class Form(db.Document):
    '''Primary storage for Checklist/Incident Forms.
    Defines the following attributes:

    :attr:`events` a list of refernces to :class:`core.documents.Event` objects
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

    name = db.StringField(required=True)
    prefix = db.StringField()
    form_type = db.StringField(choices=FORM_TYPES)
    groups = db.ListField(db.EmbeddedDocumentField('FormGroup'))
    events = db.ListField(db.ReferenceField('Event'))
    deployment = db.ReferenceField(Deployment)

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

    def clean(self):
        '''Ensures all :class: `core.documents.FormGroup` instances for this
        document have their slug set.'''
        for group in self.groups:
            if not group.slug:
                group.slug = slugify_unicode(group.name).lower()
        return super(Form, self).clean()


# Submissions
class Submission(db.DynamicDocument):
    '''Submissions represent data collected by participants in response to
    questions in Checklist and Critical Incident forms. Submissions are created
    prior to data input and are updated whenever data is received. The only
    exception is for the storage of Critical Incident reports which create
    submissions when data input is received.

    The :class:`core.documents.Submission` model
    is a :class:`mongoengine.DynamicDocument` and hence, most of it's
    functionality isn't stored within the model and gets defined at run time
    depending on the configuration of forms, form groups and form fields.

    :attr:`updated` is a :class:`mongoengine.db.DateTimeField` that stores the
    last time the submission was updated.

    :attr:`created` is a :class:`mongoengine.db.DateTimeField` that stores the
    date of creation for the submission.

    :attr:`contributor` stores the contributing participant for
    this submission.

    :attr:`form` provides a reference to the form that the submission was
    made for.
    '''

    form = db.ReferenceField('Form')
    contributor = db.ReferenceField('Participant')
    location = db.ReferenceField('Location')
    created = db.DateTimeField()
    updated = db.DateTimeField()
    completion = db.DictField()
    deployment = db.ReferenceField(Deployment)

    meta = {
        'queryset_class': SubmissionQuerySet,
    }

    def _update_completion_status(self):
        '''Computes the completion status of each form group for a submission.
        Should be called automatically on save, preferably in the `clean`
        method.'''
        for group in self.form.groups:
            completed = [f.name in self for f in group.fields]

            if all(completed):
                self.completion[group] = 'Complete'
            elif any(completed):
                self.completion[group] = 'Partial'
            else:
                self.completion[group] = 'Missing'


# Locations
class Sample(db.Document):
    '''Samples allow for the storage of groups of Locations that can be used
    to create samples for analysis or data management.'''

    name = db.StringField()
    events = db.ListField(db.ReferenceField('Event'))
    deployment = db.ReferenceField(Deployment)

    meta = {
        'indexes': [
            ['events']
        ]
    }


class LocationTypeAncestor(db.EmbeddedDocument):
    '''An embedded document used by the :class:`core.document.LocationType`
    model for storing denormalized ancestry data'''

    name = db.StringField()


class LocationType(db.Document):
    '''Stores the type describing the administrative level of a Location
    :attr ancestors_ref: This stores a list references to ancestor
    loction types as documented in
    http://docs.mongodb.org/manual/tutorial/model-tree-structures/'''

    name = db.StringField()
    ancestors_ref = db.ListField(db.ReferenceField('LocationType'))
    on_submissions_view = db.BooleanField(default=False)
    on_dashboard_view = db.BooleanField(default=False)
    on_analysis_view = db.BooleanField(default=False)
    events = db.ListField(db.ReferenceField('Event'))
    slug = db.StringField()
    deployment = db.ReferenceField(Deployment)

    meta = {
        'indexes': [
            ['events']
        ]
    }

    @classmethod
    def get_root_for_event(cls, event):
        return cls.objects.get(events=event, __raw__={'ancestors_ref': []})

    def clean(self):
        if not self.slug:
            self.slug = slugify_unicode(self.name).lower()
        return super(LocationType, self).clean()

    def get_children(self):
        return LocationType.objects(ancestors_ref=self)

    def __unicode__(self):
        return self.name


class LocationAncestor(db.EmbeddedDocument):
    '''An embedded document for storing location ancestors data to enable
    fast retrieval of data fields'''
    name = db.StringField()
    location_type = db.StringField()


class Location(db.Document):

    '''A store for Locations'''

    name = db.StringField()
    code = db.StringField()
    location_type = db.StringField()
    coords = db.GeoPointField()
    ancestors_ref = db.ListField(db.ReferenceField('Location'))
    ancestors = db.ListField(db.EmbeddedDocumentField('LocationAncestor'))
    samples = db.ListField(db.ReferenceField('Sample'))
    events = db.ListField(db.ReferenceField('Event'))
    deployment = db.ReferenceField(Deployment)

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
        ],
        'queryset_class': LocationQuerySet
    }

    @classmethod
    def get_root_for_event(cls, event):
        return cls.objects.get(events=event, __raw__={'ancestors_ref': []})

    def get_children(self):
        return Location.objects(ancestors_ref=self)

    def __unicode__(self):
        return self.name


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
    events = db.ListField(db.ReferenceField('Event'))
    deployment = db.ReferenceField(Deployment)

    def __unicode__(self):
        return self.name


class VersionSequenceField(db.SequenceField):
    '''A subclass of :class: `mongoengine.fields.SequenceField` for
    automatically updating version numbers'''

    def get_sequence_name(self):
        obj_id = self.owner_document.submission._id
        return '_'.join(('version', 'seq', str(obj_id)))


class SubmissionVersion(db.Document):
    '''Stores versions of :class: `core.documents.Submission`
    instances'''
    submission = db.ReferenceField(Submission, required=True)
    data = db.StringField(required=True)
    version = VersionSequenceField()
    timestamp = db.DateTimeField(default=datetime.utcnow())
    changed_by = db.ReferenceField(User, required=True)
    deployment = db.ReferenceField(Deployment)

    meta = {
        'ordering': ['-version', '-timestamp']
    }


class SubmissionComment(db.Document):
    '''Stores user comments.'''
    submission = db.ReferenceField(Submission)
    user = db.ReferenceField(User)
    comment = db.StringField()
    submit_date = db.DateTimeField(default=datetime.utcnow())
    deployment = db.ReferenceField(Deployment)
