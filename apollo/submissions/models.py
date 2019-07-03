# -*- coding: utf-8 -*-
from flask_babelex import lazy_gettext as _
from geoalchemy2 import Geometry
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy_utils import ChoiceType

from apollo.core import db
from apollo.dal.models import BaseModel
from apollo.utils import current_timestamp

FLAG_STATUSES = {
    'no_problem': ('0', _('No Problem')),
    'problem': ('2', _('Problem')),
    'verified': ('4', _('Verified')),
    'rejected': ('5', _('Rejected'))
}

QUALITY_STATUSES = {
    'OK': '0',
    'FLAGGED': '2',
    'VERIFIED': '3'
}

FLAG_CHOICES = (
    ('0', _('OK')),
    ('-1', _('MISSING')),
    ('2', _('FLAGGED')),
    ('4', _('VERIFIED')),
)

STATUS_CHOICES = (
    ('', _('Status')),
    ('0', _('Status — No Problem')),
    ('2', _('Status — Unverified')),
    ('4', _('Status — Verified')),
    ('5', _('Status — Rejected'))
)


class Submission(BaseModel):
    SUBMISSION_TYPES = (
        ('O', _('Observer submission')),
        ('M', _('Master submission')),
    )

    QUARANTINE_STATUSES = (
        ('', _('None')),
        ('A', _('All')),
        ('R', _('Results')),
    )

    INCIDENT_STATUSES = (
        (None, _('Unmarked')),
        ('citizen', _('Citizen Report')),
        ('confirmed', _('Confirmed')),
        ('rejected', _('Rejected'))
    )

    VERIFICATION_STATUSES = (
        ('', _('Unconfirmed')),
        ('4', _('Confirmed'))
    )

    VERIFICATION_OPTIONS = {
        'VERIFIED': '4',
        'REJECTED': '5'
    }

    __table_args__ = (
        db.Index('submission_data_idx', 'data', postgresql_using='gin'),
    )
    __tablename__ = 'submission'

    id = db.Column(db.Integer, primary_key=True)
    deployment_id = db.Column(db.Integer, db.ForeignKey(
        'deployment.id', ondelete='CASCADE'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey(
        'event.id', ondelete='CASCADE'), nullable=False)
    form_id = db.Column(db.Integer, db.ForeignKey(
        'form.id', ondelete='CASCADE'), nullable=False)
    participant_id = db.Column(db.Integer, db.ForeignKey(
        'participant.id', ondelete='CASCADE'))
    location_id = db.Column(db.Integer, db.ForeignKey(
        'location.id', ondelete='CASCADE'), nullable=False)
    data = db.Column(JSONB, default={})
    extra_data = db.Column(JSONB)
    submission_type = db.Column(ChoiceType(SUBMISSION_TYPES))
    created = db.Column(db.DateTime, default=current_timestamp)
    updated = db.Column(db.DateTime, onupdate=current_timestamp)
    sender_verified = db.Column(db.Boolean, default=True)
    quarantine_status = db.Column(ChoiceType(QUARANTINE_STATUSES), default='')
    verification_status = db.Column(
        ChoiceType(VERIFICATION_STATUSES),
        default=VERIFICATION_STATUSES[0][0])
    incident_description = db.Column(db.String)
    incident_status = db.Column(ChoiceType(INCIDENT_STATUSES))
    overridden_fields = db.Column(ARRAY(db.String), default=[])
    last_phone_number = db.Column(db.String)
    deployment = db.relationship(
        'Deployment',
        backref=db.backref('submissions', cascade='all, delete',
                           passive_deletes=True))
    event = db.relationship(
        'Event',
        backref=db.backref('submissions', cascade='all, delete',
                           passive_deletes=True))
    form = db.relationship(
        'Form',
        backref=db.backref('submissions', cascade='all, delete',
                           passive_deletes=True))
    location = db.relationship(
        'Location',
        backref=db.backref('submissions', cascade='all, delete',
                           passive_deletes=True))
    participant = db.relationship(
        'Participant',
        backref=db.backref('submissions', cascade='all, delete',
                           passive_deletes=True))
    conflicts = db.Column(JSONB)
    unreachable = db.Column(db.Boolean, default=False, nullable=False)
    geom = db.Column(Geometry('POINT', srid=4326))

    @classmethod
    def init_submissions(cls, event, form, role, location_type):
        from apollo.participants.models import Participant

        if form.form_type != 'CHECKLIST':
            return

        location_set_id = location_type.location_set_id
        participant_set_id = role.participant_set_id

        if location_set_id != event.location_set_id:
            return

        if participant_set_id != event.participant_set_id:
            return

        deployment_id = event.deployment_id

        for participant in Participant.query.filter_by(role_id=role.id):
            if not participant.location_id:
                continue

            if location_type.id == participant.location.location_type.id:
                location = participant.location
            else:
                try:
                    location = next(a for a in participant.location.ancestors()
                                    if a.location_type.id == location_type.id)
                    if not location:
                        return
                except StopIteration:
                    return

            obs_submission = cls.query.filter_by(
                form_id=form.id, participant_id=participant.id,
                location_id=location.id, deployment_id=deployment_id,
                event_id=event.id, submission_type='O').first()

            if not obs_submission:
                obs_submission = cls(
                    form_id=form.id, participant_id=participant.id,
                    location_id=location.id, deployment_id=deployment_id,
                    event_id=event.id, submission_type='O',
                    data={})
                obs_submission.save()

            master_submission = cls.query.filter_by(
                form_id=form.id, participant_id=None,
                location_id=location.id, deployment_id=deployment_id,
                event_id=event.id, submission_type='M').first()

            if not master_submission:
                master_submission = cls(
                    form_id=form.id, participant_id=None,
                    location_id=location.id, deployment_id=deployment_id,
                    event_id=event.id, submission_type='M', data={})
                master_submission.save()

    def update_related(self, data):
        '''
        Given a dict used to update the submission,
        update the master with the data not in conflict,
        and update all related submissions with the
        conflict data
        '''
        if self.form.form_type == 'INCIDENT':
            return

        if not self.form.track_data_conflicts:
            return

        conflict_tags = self.compute_conflict_tags(data.keys())
        subset = {k: v for k, v in data.items() if k not in conflict_tags}

        master = self.master
        master.data = subset

        siblings = self.siblings
        self.conflicts = trim_conflicts(self, conflict_tags, data.keys())
        master.conflicts = trim_conflicts(master, conflict_tags, data.keys())
        for sibling in siblings:
            sibling.conflicts = trim_conflicts(
                sibling, conflict_tags, data.keys())

        db.session.begin(nested=True)
        db.session.add_all([self, master])
        db.session.add_all(siblings)
        db.session.commit()

    def update_master_offline_status(self):
        siblings = self.siblings
        master_offline_status = self.master.unreachable

        if siblings:
            if (
                all([s.unreachable for s in self.siblings]) and
                self.unreachable
            ):
                self.master.unreachable = True
        else:
            if self.unreachable:
                self.master.unreachable = True

        # if the offline status changed in any way
        if master_offline_status != self.master.unreachable:
            db.session.add(self.master)

    def compute_conflict_tags(self, tags=None):
        # don't compute if the 'track conflicts' flag is not set
        # on the form
        if not self.form.track_data_conflicts:
            return []

        # or if the form is an incident form
        if self.form.form_type == 'INCIDENT':
            return []

        # check only a subset of the tags
        tags_to_check = set(self.form.tags) - set(self.overridden_fields)
        if tags:
            tags_to_check = tags_to_check.intersection(set(tags))

        # conflict query
        params = [
            sa.func.bool_or(
                sa.and_(
                    Submission.data.has_key(tag),   # noqa
                    sa.not_(Submission.data.contains({tag: self.data[tag]}))
                )
            ).label(tag)
            for tag in tags_to_check
            if tag in self.data
        ]

        if not params:
            return []
        siblings = self.__siblings()
        result = siblings.with_entities(*params).one()

        return [k for k, v in result._asdict().items() if v]

    def get_incident_status_display(self):
        d = dict(self.INCIDENT_STATUSES)
        return d.get(self.incident_status, _('Unmarked'))

    def _compute_completion(self, group_tags):
        are_empty_values = [
            # TODO: check the empty values
            self.data.get(tag) not in (None, '', [])
            for tag in group_tags
        ] if self.data else []
        if are_empty_values and all(are_empty_values):
            return 'Complete'
        elif any(are_empty_values):
            return 'Partial'
        else:
            return 'Missing'

    def completion(self, group_name):
        group_tags = self.form.get_group_tags(group_name)
        if (
            self.form.form_type == 'INCIDENT'
                or not self.form.track_data_conflicts
        ):
            return self._compute_completion(group_tags)
        else:
            conflict_tags = set(group_tags).intersection(
                set(self.conflicts or []))
            if conflict_tags:
                return 'Conflict'
            return self._compute_completion(group_tags)

    def __siblings(self):
        '''Returns siblings as a SQLA query object'''
        return Submission.query.filter(
            Submission.deployment_id == self.deployment_id,
            Submission.event_id == self.event_id,
            Submission.form_id == self.form_id,
            Submission.location_id == self.location_id,
            Submission.submission_type == 'O',
            Submission.id != self.id
        )

    def __master(self):
        return Submission.query.filter(
            Submission.deployment_id == self.deployment_id,
            Submission.event_id == self.event_id,
            Submission.form_id == self.form_id,
            Submission.location_id == self.location_id,
            Submission.submission_type == 'M'
        ).first()

    @property
    def siblings(self):
        '''Returns siblings as POPOs'''
        if not hasattr(self, '_siblings'):
            self._siblings = self.__siblings().all()

        return self._siblings

    @property
    def master(self):
        if self.submission_type == 'M':
            return self

        if self.form.form_type == 'INCIDENT':
            self._master = None

        if not hasattr(self, '_master'):
            self._master = Submission.query.filter(
                Submission.deployment_id == self.deployment_id,
                Submission.event_id == self.event_id,
                Submission.form_id == self.form_id,
                Submission.location_id == self.location_id,
                Submission.submission_type == 'M'
            ).first()

        return self._master


class SubmissionComment(BaseModel):
    __tablename__ = 'submission_comment'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey(
        'submission.id', ondelete='CASCADE'), nullable=False)
    submission = db.relationship(
        'Submission',
        backref=db.backref('comments', cascade='all, delete',
                           passive_deletes=True))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='submission_comments')
    comment = db.Column(db.String)
    submit_date = db.Column(db.DateTime, default=current_timestamp)
    deployment_id = db.Column(db.Integer, db.ForeignKey(
        'deployment.id', ondelete='CASCADE'), nullable=False)
    deployment = db.relationship(
        'Deployment',
        backref=db.backref('submission_comments', cascade='all, delete',
                           passive_deletes=True))


class SubmissionVersion(BaseModel):
    __tablename__ = 'submission_version'

    CHANNEL_CHOICES = (
        ('SMS', _('SMS')),
        ('WEB', _('Web')),
        ('API', _('API')),
        ('ODK', _('ODK')),
    )
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey(
        'submission.id', ondelete='CASCADE'), nullable=False)
    data = db.Column(JSONB)
    submission = db.relationship(
        'Submission',
        backref=db.backref('versions', cascade='all, delete',
                           passive_deletes=True))
    timestamp = db.Column(db.DateTime, default=current_timestamp)
    channel = db.Column(ChoiceType(CHANNEL_CHOICES))
    deployment_id = db.Column(db.Integer, db.ForeignKey(
        'deployment.id', ondelete='CASCADE'), nullable=False)
    deployment = db.relationship(
        'Deployment',
        backref=db.backref('submission_versions', cascade='all, delete',
                           passive_deletes=True))
    identity = db.Column(db.String, default='unknown', nullable=False)


def trim_conflicts(submission, conflict_tags, data_keys):
    '''remove keys that were updated and no longer in conflict
    and add keys that are new conflicts'''
    conflict_keys = set(conflict_tags)

    # these were updated, they are not in conflict any longer
    updated_unconflicted_keys = set(data_keys) - set(conflict_tags)
    new_conflicts = set(submission.conflicts) - updated_unconflicted_keys \
        if submission.conflicts else set()

    return sorted(new_conflicts.union(conflict_keys))
