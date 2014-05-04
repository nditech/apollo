# coding: utf-8
from ..core import db
from ..deployments.models import Deployment, Event
from ..formsframework.models import Form
from ..formsframework.parser import Comparator, Evaluator
from ..helpers import compute_location_path
from ..locations.models import Location
from ..participants.models import Participant
from ..users.models import User
from datetime import datetime
from flask.ext.babel import lazy_gettext as _
from flask.ext.mongoengine import BaseQuerySet
from mongoengine import Q
from pandas import DataFrame, isnull

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

    :attr:`completion` is a dictionary whose keys are the names of the
    groups defined on :attr:`form` (if any) and whose values are (as at the
    time of writing this) are Complete, Partial or Missing, based on if all
    fields within that group have been filled out. Please see the method
    _update_completion_status() for details.

    :attr:`location_name_path` is a dictionary with location type names as
    keys and actual location names as values. Since MongoDB doesn't support
    joins, it was created to be a precomputed shortcut to using the location
    hierarchy in queries and views without needing several database lookups.

    :attr:`sender_verified` is set to True if the sender of a submission has
    been verified. For instance, if it was received from a known phone number
    in the case of SMS, or a known user account (either via the UI or API).

    :attr:`quality_checks` stores the precomputed value of different logical
    checks (created at runtime, so we can't predict in advance). An example
    logical check would be: for this submission, was the total number of votes
    greater than the total number of registered voters?

    :attr:`verification_status` stores the overall result of all the logical
    checks: are there problems with this data, or is everything ok, or not
    enough data to have an opinion? see STATUS_CHOICES for the full list of
    possible values.

    IMPORTANT: submissions for incident forms get a few more dynamic fields:
        - status: whether the incident was confirmed/rejected etc
        - witness: whether the contributor actually witnessed the incident,
            was reported by a third party, etc
    '''

    SUBMISSION_TYPES = (
        ('O', _(u'Observer Submission')),
        ('M', _(u'Master Submission')),
    )

    form = db.ReferenceField(Form)
    contributor = db.ReferenceField(Participant)
    location = db.ReferenceField(Location)
    created = db.DateTimeField()
    updated = db.DateTimeField()
    completion = db.DictField()
    location_name_path = db.DictField()
    sender_verified = db.BooleanField(default=True)
    quality_checks = db.DictField()
    verification_status = db.StringField()
    submission_type = db.StringField(
        choices=SUBMISSION_TYPES, default='O', required=True)

    deployment = db.ReferenceField(Deployment)
    event = db.ReferenceField(Event)

    meta = {
        'queryset_class': SubmissionQuerySet,
    }

    def _update_completion_status(self):
        '''Computes the completion status of each form group for a submission.
        Should be called automatically on save, preferably in the `clean`
        method.'''
        for group in self.form.groups:
            completed = [getattr(self, f.name, None) is not None
                         for f in group.fields]

            if all(completed):
                self.completion[group.name] = 'Complete'
            elif any(completed):
                self.completion[group.name] = 'Partial'
            else:
                self.completion[group.name] = 'Missing'

    def _update_data_fields(self):
        '''This little utility simply sets any boolean fields to None.
        Have found that having boolean fields have the value False
        causes problems in analysis.'''
        fields = [
            field for group in self.form.groups
            for field in group.fields]

        boolean_fields = [
            field for field in fields if field.represents_boolean]
        single_value_fields = [
            field for field in fields
            if field.options is not None and
            field.allows_multiple_values is False]

        for field in boolean_fields:
            if not getattr(self, field.name, None):
                # dictionary-style access will fail. it's a MongoEngine issue
                # self[field.name] = None
                setattr(self, field.name, None)

        for field in single_value_fields:
            value = getattr(self, field.name, '')
            if value == '':
                setattr(self, field.name, None)
            elif isinstance(value, int):
                setattr(self, field.name, value)
            elif isinstance(value, str) and value.isdigit():
                setattr(self, field.name, int(value))

    def _compute_verification(self):
        '''Precomputes the logical checks on the submission.'''
        if self.submission_type != 'M':
            # only for master submissions
            return

        verified_flag = FLAG_STATUSES['verified'][0]
        rejected_flag = FLAG_STATUSES['rejected'][0]

        comparator = Comparator()

        NO_DATA = 0
        OK = 1
        UNOK = 2

        flags_statuses = []
        for flag in self.form.quality_checks:
            evaluator = Evaluator(self)

            try:
                lvalue = evaluator.eval(flag['lvalue'])
                rvalue = evaluator.eval(flag['rvalue'])

                # the comparator setting expresses the relationship between
                # lvalue and rvalue
                if flag['comparator'] == 'pctdiff':
                    # percentage difference between lvalue and rvalue
                    try:
                        diff = abs(lvalue - rvalue) / float(
                            max([lvalue, rvalue]))
                    except ZeroDivisionError:
                        diff = 0
                elif flag['comparator'] == 'pct':
                    # absolute percentage
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
                self.quality_checks[flag['storage']] = flag_setting
            except TypeError:
                # no sufficient data
                # setattr(self, flag['storage'], None)
                try:
                    self.quality_checks.pop(flag['storage'])
                except KeyError:
                    pass
                flags_statuses.append(NO_DATA)

        # compare all flags and depending on the values, set the status
        if not self.verification_status in [verified_flag, rejected_flag]:
            if all(map(lambda i: i == NO_DATA, flags_statuses)):
                self.verification_status = None
            elif any(map(lambda i: i == UNOK, flags_statuses)):
                self.verification_status = FLAG_STATUSES['problem'][0]
            elif any(map(lambda i: i == OK, flags_statuses)):
                self.verification_status = FLAG_STATUSES['no_problem'][0]

    def clean(self):
        # update location name path if it does not exist.
        # unlike for participants, submissions aren't 'mobile', that is,
        # there doesn't seem to be a use case for transferring submissions.
        # at least, not at the time of writing
        if not self.location_name_path:
            self.location_name_path = compute_location_path(self.location)

        # cleanup data fields
        self._update_data_fields()

        # update completion status
        self._update_completion_status()

        # and compute the verification
        self._compute_verification()

        # update the `updated` timestamp
        self.updated = datetime.utcnow()

    @property
    def master(self):
        if self.form.form_type == 'INCIDENT':
            return None

        if not hasattr(self, '_master'):
            try:
                self._master = Submission.objects.get(
                    form=self.form,
                    location=self.location,
                    created__gte=self.created.combine(self.created,
                                                      self.created.min.time()),
                    created__lte=self.created.combine(self.created,
                                                      self.created.max.time()),
                    submission_type='M',
                    deployment=self.deployment,
                    event=self.event
                )
            except self.DoesNotExist:
                self._master = Submission.objects.create(
                    form=self.form,
                    location=self.location,
                    created=self.created,
                    submission_type='M',
                    deployment=self.deployment,
                    event=self.event
                )
        return self._master

    @property
    def siblings(self):
        if not hasattr(self, '_siblings'):
            self._siblings = Submission.objects(
                form=self.form,
                location=self.location,
                created__gte=self.created.combine(self.created,
                                                  self.created.min.time()),
                created__lte=self.created.combine(self.created,
                                                  self.created.max.time()),
                submission_type='O',               # exclude master
                deployment=self.deployment,
                event=self.event,
                pk__ne=self.pk
            )
        return self._siblings

    @property
    def versions(self):
        return SubmissionVersion.objects(submission=self)

    @property
    def comments(self):
        return SubmissionComment.objects(submission=self)


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
