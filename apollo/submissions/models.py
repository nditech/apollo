# -*- coding: utf-8 -*-
from flask_babelex import lazy_gettext as _
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, array
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

    __tablename__ = 'submission'

    id = db.Column(
        db.Integer, db.Sequence('submission_id_seq'), primary_key=True)
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
    confidence = db.Column(JSONB, default={})
    quality_assurance_status = db.Column(JSONB, default={})
    overridden_fields = db.Column(ARRAY(db.String), default=[])
    deployment = db.relationship('Deployment', backref='submissions')
    event = db.relationship('Event', backref='submissions')
    form = db.relationship('Form', backref='submissions')
    location = db.relationship('Location', backref='submissions')
    participant = db.relationship('Participant', backref='submissions')

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
                    event_id=event.id, submission_type='O', data={},
                    quality_assurance_status={})
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
                    confidence={}, quality_assurance_status={})
                master_submission.save()

    def get_incident_status_display(self):
        d = dict(self.INCIDENT_STATUSES)
        return d.get(self.incident_status, _('Unmarked'))

    def completion(self, group_name):
        # TODO: fix conflict status
        group_tags = self.form.get_group_tags(group_name)
        siblings = self.siblings
        if len(siblings) == 0:
            subset = [
                self.data.get(tag) not in (None, '', [])
                for tag in group_tags] if self.data else []

            if subset and all(subset):
                return 'Complete'
            elif any(subset):
                return 'Partial'
            else:
                return 'Missing'
        else:
            if self.overridden_fields:
                tags_to_check = set(group_tags) - set(self.overridden_fields)
            else:
                tags_to_check = group_tags

            all_submissions = [self] + siblings
            for tag in tags_to_check:
                check_data = [sub.data.get(tag) for sub in all_submissions]
                check = {
                    frozenset(item)
                    if isinstance(item, list) else item
                    for item in check_data}
                if len(check) > 1:
                    return 'Conflict'

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

    @classmethod
    def _compute_confidence(cls, submission, siblings=None):
        if submission.submission_type != 'M':
            return

        quarantined_status_flags = [
            i[0] for i in
            [s for s in cls.QUARANTINE_STATUSES if s[0]]
        ]
        if not siblings:
            siblings = submission.__siblings().filter(
                ~Submission.quarantine_status.in_(quarantined_status_flags)
            ).all()
        tags = submission.form.tags

        confidence = {}

        for tag in tags:
            score = None
            if submission.overridden_fields:
                if tag in submission.overridden_fields:
                    score = 1
                    confidence[tag] = score
                    continue

            values = [frozenset(value) if isinstance(value, list) else value
                      for value in [sib.data.get(tag) for sib in siblings]]
            unique = list(set(values))

            if values and len(unique) == 1 and unique[0] is not None:
                # all values agree and are not None
                score = 1
            elif values and len(unique) == 1 and not unique[0]:
                # all values agree and are None
                score = None
            else:
                n_values = [v for v in values if v is not None]
                n_unique = list(set(n_values))
                if len(n_unique) == 0 or len(n_unique) > 1:
                    # if there are no values or the number of values
                    # is greater
                    score = 0
                else:
                    try:
                        score = len(n_values) / len(values)
                    except ZeroDivisionError:
                        score = 0

            confidence[tag] = score

        return confidence

    @classmethod
    def _update_master(cls, submission):
        '''Updates a master submission data'''
        master = submission.__master()
        if not master or master.id == submission.id:
            return

        # get fields that have not been overridden
        if master.overridden_fields:
            form_tags = [
                f for f in submission.form.tags
                if f not in master.overridden_fields
            ]
        else:
            form_tags = submission.form.tags

        master_data = master.data.copy() if master.data else {}
        changed = False

        # use siblings that have not been quarantined
        quarantined_status_flags = [
            i[0] for i in
            [s for s in cls.QUARANTINE_STATUSES if s[0]]
        ]
        siblings = submission.__siblings().filter(
            ~Submission.quarantine_status.in_(quarantined_status_flags)
        ).all()

        for tag in form_tags:
            submission_field_value = submission.data.get(tag)
            sibling_field_values = [sib.data.get(tag) for sib in siblings]

            if submission.quarantine_status:
                submission_field_value = None

            all_values = [submission_field_value] + sibling_field_values
            non_null_values = [v for v in all_values if v is not None]

            # reduce this to a set of unique values
            hashable = [frozenset(v) if isinstance(v, list) else v for v in non_null_values]
            unique_values = set(hashable)

            # if the number of unique values is 0,
            # there are no non-null values. if it is
            # 1, then all siblings share the same value
            # if it is more than 1, then there are
            # conflicts. only update the master in the
            # second case
            if len(unique_values) == 1:
                v = unique_values.pop()
                v = list(v) if isinstance(v, frozenset) else v
                master_data[tag] = v
                changed = True

        confidence = cls._compute_confidence(master, [submission] + siblings)

        if changed:
            cls.query.filter_by(id=master.id).update(
                {'data': master_data, 'confidence': confidence},
                synchronize_session=False
            )
            db.session.commit()


class SubmissionComment(BaseModel):
    __tablename__ = 'submission_comment'

    id = db.Column(
        db.Integer, db.Sequence('submission_comment_id_seq'),
        primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey(
        'submission.id', ondelete='CASCADE'), nullable=False)
    submission = db.relationship('Submission', backref='comments')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='submission_comments')
    comment = db.Column(db.String)
    submit_date = db.Column(db.DateTime, default=current_timestamp)
    deployment_id = db.Column(db.Integer, db.ForeignKey(
        'deployment.id', ondelete='CASCADE'), nullable=False)
    deployment = db.relationship('Deployment', backref='submission_comments')


class SubmissionVersion(BaseModel):
    __tablename__ = 'submission_version'

    CHANNEL_CHOICES = (
        ('SMS', _('SMS')),
        ('WEB', _('Web')),
        ('API', _('API')),
        ('ODK', _('ODK')),
    )
    id = db.Column(
        db.Integer, db.Sequence('submission_version_id_seq'),
        primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey(
        'submission.id', ondelete='CASCADE'), nullable=False)
    data = db.Column(JSONB)
    submission = db.relationship('Submission', backref='versions')
    timestamp = db.Column(db.DateTime, default=current_timestamp)
    channel = db.Column(ChoiceType(CHANNEL_CHOICES))
    deployment_id = db.Column(db.Integer, db.ForeignKey(
        'deployment.id', ondelete='CASCADE'), nullable=False)
    deployment = db.relationship('Deployment', backref='submission_versions')
    identity = db.Column(db.String, default='unknown', nullable=False)
