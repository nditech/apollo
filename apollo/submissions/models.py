# coding: utf-8
from ..core import db
from ..deployments.models import Deployment
from ..formsframework.models import Form
from ..formsframework.parser import Comparator, Evaluator
from ..helpers import compute_location_path
from ..locations.models import Location
from ..participants.models import Participant
from ..users.models import User
from datetime import datetime, timedelta
from flask.ext.babel import lazy_gettext as _
from flask.ext.mongoengine import BaseQuerySet
from mongoengine import Q
from pandas import DataFrame, isnull

DEFAULT_SUBMISSION_RANGE = timedelta(hours=3)

FLAG_STATUSES = {
    'no_problem': ('0', _('No Problem')),
    'problem': ('2', _('Problem')),
    'serious_problem': ('3', _('Serious Problem')),
    'verified': ('4', _('Verified')),
    'rejected': ('5', _('Rejected'))
}

FLAG_CHOICES = (
    ('0', _('No Problem')),
    ('2', _('Problem')),
    ('3', _('Serious Problem')),
    ('4', _('Verified')),
    ('5', _('Rejected'))
)

STATUS_CHOICES = (
    ('', _(u'Status')),
    ('0', _(u'Status — No Problem')),
    ('2', _(u'Status — Unverified')),
    ('4', _(u'Status — Verified')),
    ('5', _(u'Status — Rejected'))
)


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

        df = DataFrame(list(qs.as_pymongo())).convert_objects(
            convert_numeric=True)
        if df.empty:
            return df

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
    location_name_path = db.DictField()
    sender_verified = db.BooleanField(default=True)
    verification_flags = db.DictField()
    verification = db.StringField()

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
                self.completion[group.name] = 'Complete'
            elif any(completed):
                self.completion[group.name] = 'Partial'
            else:
                self.completion[group.name] = 'Missing'

    def _compute_verification(self):
        if self.contributor is not None:
            return

        verified_flag = FLAG_STATUSES['verified'][0]
        rejected_flag = FLAG_STATUSES['rejected'][0]

        comparator = Comparator()

        NO_DATA = 0
        OK = 1
        UNOK = 2

        flags_statuses = []
        for flag in self.form.verification_flags:
            evaluator = Evaluator(self)

            try:
                lvalue = evaluator.eval(flag['lvalue'])
                rvalue = evaluator.eval(flag['rvalue'])

                if flag['comparator'] == 'pctdiff':
                    try:
                        diff = abs(lvalue - rvalue) / float(max([lvalue, rvalue]))
                    except ZeroDivisionError:
                        diff = 0
                elif flag['comparator'] == 'pct':
                    try:
                        diff = float(lvalue) / float(rvalue)
                    except ZeroDivisionError:
                        diff = 0
                else:
                    # value-based comparator
                    diff = abs(lvalue - rvalue)

                # evaluate conditions and set flag appropriately
                if comparator.eval(flag['okay'], diff):
                    flag_setting = FLAG_STATUSES['no_problem'][0]
                    flags_statuses.append(OK)
                elif comparator.eval(flag['serious'], diff):
                    flag_setting = FLAG_STATUSES['serious_problem'][0]
                    flags_statuses.append(UNOK)
                elif comparator.eval(flag['problem'], diff):
                    flag_setting = FLAG_STATUSES['problem'][0]
                    flags_statuses.append(UNOK)
                else:
                    # if we have no way of determining, we assume it's okay
                    flag_setting = FLAG_STATUSES['no_problem'][0]
                    flags_statuses.append(OK)

                # setattr(self, flag['storage'], flag_setting)
                self.verification_flags[flag['storage']] = flag_setting
            except TypeError:
                # no sufficient data
                # setattr(self, flag['storage'], None)
                try:
                    self.verification_flags.pop(flag['storage'])
                except KeyError:
                    pass
                flags_statuses.append(NO_DATA)

        # compare all flags and depending on the values, set the status
        if not self.verification in [verified_flag, rejected_flag]:
            if all(map(lambda i: i == NO_DATA, flags_statuses)):
                self.verification = None
            elif any(map(lambda i: i == UNOK, flags_statuses)):
                self.verification = FLAG_STATUSES['problem'][0]
            elif any(map(lambda i: i == OK, flags_statuses)):
                self.verification = FLAG_STATUSES['no_problem'][0]

    def clean(self):
        # update location name path if it does not exist.
        # unlike for participants, submissions aren't 'mobile', that is,
        # there doesn't seem to be a use case for transferring submissions.
        # at least, not at the time of writing
        if not self.location_name_path:
            self.location_name_path = compute_location_path(self.location)

        # update completion status
        self._update_completion_status()

        # and compute the verification
        self._compute_verification()

    @property
    def master(self):
        if self.form.form_type == 'INCIDENT':
            return None

        if not hasattr(self, '_master'):
            upper_bound = self.created + DEFAULT_SUBMISSION_RANGE
            lower_bound = self.created - DEFAULT_SUBMISSION_RANGE

            self._master = Submission.objects.get(
                form=self.form,
                location=self.location,
                created__lte=upper_bound,
                created__gte=lower_bound,
                contributor=None,
            )
        return self._master

    @property
    def siblings(self):
        if not hasattr(self, '_siblings'):
            upper_bound = self.created + DEFAULT_SUBMISSION_RANGE
            lower_bound = self.created - DEFAULT_SUBMISSION_RANGE

            self._siblings = Submission.objects(
                form=self.form,
                location=self.location,
                created__lte=upper_bound,
                created__gte=lower_bound,
                contributor__ne=None,               # exclude master
                pk__ne=self.pk
            )
        return self._siblings

    @property
    def versions(self):
        if not hasattr(self, '_versions'):
            self._versions = SubmissionVersion.objects(submission=self)
        return self._versions


class SubmissionComment(db.Document):
    '''Stores user comments.'''
    submission = db.ReferenceField(Submission)
    user = db.ReferenceField(User)
    comment = db.StringField()
    submit_date = db.DateTimeField(default=datetime.utcnow())

    deployment = db.ReferenceField(Deployment)


class SubmissionVersion(db.Document):
    '''Stores versions of :class:`core.documents.Submission`
    instances'''
    CHANNEL_CHOICES = (
        ('SMS', _('SMS')),
        ('Web', _('Web')),
        ('API', _('API'))
    )
    submission = db.ReferenceField(Submission, required=True)
    data = db.StringField(required=True)
    timestamp = db.DateTimeField(default=datetime.utcnow())
    channel = db.StringField(choices=CHANNEL_CHOICES, required=True)
    identity = db.StringField(default='Unknown', required=True)

    deployment = db.ReferenceField(Deployment)

    meta = {
        'ordering': ['-timestamp']
    }

    @property
    def version_number(self):
        versions = list(SubmissionVersion.objects(
            deployment=self.deployment,
            submission=self.submission
        ).scalar('id'))

        return versions.index(self.id) + 1
