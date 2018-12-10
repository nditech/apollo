# -*- coding: utf-8 -*-
from flask_babelex import lazy_gettext as _
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
    ('5', _('REJECTED'))
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

    @classmethod
    def update_master(cls, submission):
        '''Update a master submission based on an observer submission's data'''
        submission_form = submission.form

        # not applicable to master submissions
        if submission.submission_type.code == 'M':
            return

        # not applicable to incident form submissions
        if submission_form.form_type == 'INCIDENT':
            return

        # get master and sibling submissions
        related_submissions = cls.query.filter(
            cls.deployment_id == submission.deployment_id,
            cls.event_id == submission.event_id,
            cls.form_id == submission.form_id,
            cls.location_id == submission.location_id,
            cls.id != submission.id)

        master = related_submissions.filter_by(submission_type='M').one()
        siblings = related_submissions.filter_by(submission_type='O')

        available_tags = set(submission_form.tags).difference(
            master.overridden_fields)

        query_params = [
            sa.func.bool_and(
                cls.data.contains({tag: submission.data.get(tag)}))
            for tag in available_tags
        ]
        if query_params:
            results = siblings.with_entities(*query_params).one()
        else:
            results = [True] * len(available_tags)

        master_data = {}
        conflicts = []

        for tag, result in zip(available_tags, results):
            if result is True or result is None:
                master_data[tag] = submission.data.get(tag)
            else:
                conflicts.append(tag)

        db.session.begin(subtransactions=True)
        cls.query.filter_by(id=master.id).update(
            {'data': master_data, 'conflicts': conflicts},
            synchronize_session=False)
        db.session.commit()

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
                    event_id=event.id, submission_type='O', data={})
                obs_submission.save()

            master_submission = cls.query.filter_by(
                form_id=form.id, participant_id=None,
                location_id=location.id, deployment_id=deployment_id,
                event_id=event.id, submission_type='M').first()

            if not master_submission:
                master_submission = cls(
                    form_id=form.id, participant_id=None,
                    location_id=location.id, deployment_id=deployment_id,
                    event_id=event.id, submission_type='M', data={},
                    conflicts=[])
                master_submission.save()

    def get_incident_status_display(self):
        d = dict(self.INCIDENT_STATUSES)
        return d.get(self.incident_status, _('Unmarked'))

    def completion(self, group_name):
        def _completion(group_fill_status):
            if all(group_fill_status):
                return 'Complete'
            elif any(group_fill_status):
                return 'Partial'

            return 'Missing'

        form = self.form
        group_tags = form.get_group_tags(group_name)
        if not group_tags:
            return
        empty_values = (None, '', [])
        group_data_filled = [
            self.data.get(tag) not in empty_values
            for tag in group_tags
        ] if self.data else []

        if form.form_type == 'CHECKLIST':
            siblings = self.__siblings()
            if siblings.count() == 0:
                return _completion(group_data_filled)
            if self.overridden_fields:
                tags = set(group_tags).difference(self.overridden_fields)
            else:
                tags = group_tags

            query_params = [
                sa.func.bool_and(
                    Submission.data.contains({tag: self.data.get(tag)}))
                for tag in tags if self.data.get(tag) is not None
            ]

            if query_params:
                result = siblings.with_entities(*query_params).one()
                false_results = [r for r in result if r is False]
                if len(false_results) > 0:
                    return 'Conflict'

            return _completion(group_data_filled)
        else:
            return _completion(group_data_filled)

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
    comment = db.Column(db.String)
    submit_date = db.Column(db.DateTime, default=current_timestamp)
    deployment_id = db.Column(db.Integer, db.ForeignKey(
        'deployment.id', ondelete='CASCADE'), nullable=False)
    deployment = db.relationship(
        'Deployment',
        backref=db.backref('submission_comments', cascade='all, delete',
                           passive_deletes=True))


class SubmissionNote(BaseModel):
    __tablename__ = 'submission_note'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey(
        'submission.id', ondelete='CASCADE'), nullable=False)
    submission = db.relationship(
        'Submission', backref='notes', cascade='all, delete')
    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False)
    user = db.relationship(
        'User',
        backref=db.backref('notes', cascade='all, delete',
                           passive_deletes=True))
    comment = db.Column(db.String)
    submit_date = db.Column(db.DateTime, default=current_timestamp)
    deployment_id = db.Column(db.Integer, db.ForeignKey(
        'deployment.id', ondelete='CASCADE'), nullable=False)
    deployment = db.relationship(
        'Deployment',
        backref=db.backref('submission_notes', cascade='all, delete',
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
