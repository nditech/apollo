from ..core import db
from ..deployments.models import Deployment
from ..formsframework.models import Form
from ..locations.models import Location
from ..participants.models import Participant
from ..users.models import User
from datetime import datetime
from flask.ext.mongoengine import BaseQuerySet
from mongoengine import Q
from pandas import DataFrame, isnull


class SubmissionQuerySet(BaseQuerySet):
    # most of the fields below are DBRef fields or not useful to
    # our particular use case.
    DEFAULT_EXCLUDED_FIELDS = [
        'id', 'form', 'created', 'updated', 'location', 'contributor',
        'deployment'
    ]
    SUBDOCUMENT_FIELDS = ['location_name_path', 'completion']

    def filter_in(self, location_spec):
        """Given a single `class`Location instance, or an iterable of
        `class`Location instances, this method restricts submissions to
        those whose location either exactly match the passed in location(s),
        or those whose location are lower than the passed in location(s) in
        the location hierarchy.

        The multiple location case is merely an extension of the single case.
        """
        if isinstance(location_spec, Location):
            # checking for a single location
            location = location_spec
            param = 'location_name_path__{}'.format(location.location_type)
            query_kwargs = {
                param: location.name
            }
            return self(Q(location=location) | Q(**query_kwargs))
        elif hasattr(location_spec, '__iter__'):
            # checking for multiple locations
            chain = Q()
            for location in location_spec:
                if not isinstance(location, Location):
                    return self.none()

                param = 'location_name_path__{}'.format(location.location_type)
                query_kwargs = {param: location.name}
                chain = Q(location=location) | Q(**query_kwargs) | chain
            return self(chain)
        # value is neither a Location instance nor an iterable
        # producing Location instances
        return self.none()

    def to_dataframe(self, selected_fields=None, excluded_fields=None):
        if excluded_fields:
            qs = self.exclude(*excluded_fields)
        else:
            qs = self.exclude(*self.DEFAULT_EXCLUDED_FIELDS)
        if selected_fields:
            qs = self.only(*selected_fields)

        df = DataFrame(list(qs.as_pymongo()))

        # do cleanup of subdocument fields
        for field in self.SUBDOCUMENT_FIELDS:
            temp = df.pop(field).tolist()
            temp2 = [i if not isnull(i) else {} for i in temp]
            df = df.join(DataFrame(temp2))

        return df


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

    form = db.ReferenceField(Form)
    contributor = db.ReferenceField(Participant)
    location = db.ReferenceField(Location)
    created = db.DateTimeField()
    updated = db.DateTimeField()
    completion = db.DictField()
    verified = db.BooleanField(default=False)
    location_name_path = db.DictField()

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


class VersionSequenceField(db.SequenceField):
    '''A subclass of :class:`mongoengine.fields.SequenceField` for
    automatically updating version numbers'''

    def get_sequence_name(self):
        obj_id = self.owner_document.submission._id
        return '_'.join(('version', 'seq', str(obj_id)))


class SubmissionVersion(db.Document):
    '''Stores versions of :class:`core.documents.Submission`
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
