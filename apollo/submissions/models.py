# -*- coding: utf-8 -*-
import sqlalchemy as sa
from depot.fields.specialized.image import UploadedImageWithThumb
from depot.fields.sqlalchemy import UploadedFileField
from flask_babel import lazy_gettext as _
from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy_utils import ChoiceType

from apollo.core import db
from apollo.dal.models import BaseModel
from apollo.utils import current_timestamp

FLAG_STATUSES = {
    "no_problem": ("0", _("No Problem")),
    "problem": ("2", _("Problem")),
    "verified": ("4", _("Verified")),
    "rejected": ("5", _("Rejected")),
}

QUALITY_STATUSES = {"OK": "0", "FLAGGED": "2", "VERIFIED": "3"}

FLAG_CHOICES = (
    ("0", _("FLAGGED")),
    ("-1", _("MISSING")),
    ("2", _("OK")),
    ("4", _("VERIFIED")),
)

STATUS_CHOICES = (
    ("", _("Status")),
    ("0", _("Status — No Problem")),
    ("2", _("Status — Unverified")),
    ("4", _("Status — Verified")),
    ("5", _("Status — Rejected")),
)


class Submission(BaseModel):
    SUBMISSION_TYPES = (
        ("O", _("Observer submission")),
        ("M", _("Master submission")),
    )

    QUARANTINE_STATUSES = (
        ("", _("None")),
        ("A", _("All")),
        ("R", _("Results")),
    )

    INCIDENT_STATUSES = (
        (None, _("Unmarked")),
        ("citizen", _("Citizen Report")),
        ("confirmed", _("Confirmed")),
        ("rejected", _("Rejected")),
    )

    VERIFICATION_STATUSES = (("", _("Unconfirmed")), ("4", _("Confirmed")))

    VERIFICATION_OPTIONS = {"VERIFIED": "4", "REJECTED": "5"}

    __table_args__ = (db.Index("submission_data_idx", "data", postgresql_using="gin"),)
    __tablename__ = "submission"

    id = db.Column(db.Integer, primary_key=True)
    deployment_id = db.Column(db.Integer, db.ForeignKey("deployment.id", ondelete="CASCADE"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id", ondelete="CASCADE"), nullable=False)
    form_id = db.Column(db.Integer, db.ForeignKey("form.id", ondelete="CASCADE"), nullable=False)
    participant_id = db.Column(db.Integer, db.ForeignKey("participant.id", ondelete="CASCADE"))
    location_id = db.Column(db.Integer, db.ForeignKey("location.id", ondelete="CASCADE"), nullable=False)
    data = db.Column(JSONB, default={})

    """
    The extra_data field contains values with the following keys:

    voting_timestamp - a date time string representing the first time any of
    the voting results were reported in ISO 8601 format

    turnout_timestamps - a mapping of field tags to a date time string
    representing the first time the turnout field was updated. The date time
    string is stored in the ISO 8601 format.

    group_timestamps - a mapping of group names to date time strings in
    ISO 8601 format representing the last time that group was updated.
    Consider a group updated if a value was saved for a field tag
    belonging to that group.
    """
    extra_data = db.Column(JSONB)
    submission_type = db.Column(ChoiceType(SUBMISSION_TYPES), index=True)
    serial_no = db.Column(db.String, index=True)
    created = db.Column(db.DateTime, default=current_timestamp)
    updated = db.Column(db.DateTime, onupdate=current_timestamp, index=True)
    participant_updated = db.Column(db.DateTime, index=True)
    sender_verified = db.Column(db.Boolean, default=True)
    quarantine_status = db.Column(ChoiceType(QUARANTINE_STATUSES), default="")
    verification_status = db.Column(ChoiceType(VERIFICATION_STATUSES), default=VERIFICATION_STATUSES[0][0])
    incident_description = db.Column(db.String)
    incident_status = db.Column(ChoiceType(INCIDENT_STATUSES))
    overridden_fields = db.Column(ARRAY(db.String), default=[])
    last_phone_number = db.Column(db.String)
    deployment = db.relationship(
        "Deployment", backref=db.backref("submissions", cascade="all, delete", passive_deletes=True)
    )
    event = db.relationship("Event", backref=db.backref("submissions", cascade="all, delete", passive_deletes=True))
    form = db.relationship(
        "Form", lazy="joined", backref=db.backref("submissions", cascade="all, delete", passive_deletes=True)
    )
    location = db.relationship(
        "Location", backref=db.backref("submissions", cascade="all, delete", passive_deletes=True)
    )
    participant = db.relationship(
        "Participant", backref=db.backref("submissions", cascade="all, delete", passive_deletes=True)
    )
    conflicts = db.Column(JSONB)
    unreachable = db.Column(db.Boolean, default=False, nullable=False)
    geom = db.Column(Geometry("POINT", srid=4326))
    verified_fields = db.Column(JSONB, default=[])

    @classmethod
    def init_submissions(cls, event, form, role, location_type, task=None):
        from apollo.participants.models import Participant

        if form.form_type != "CHECKLIST":
            return

        location_set_id = location_type.location_set_id
        participant_set_id = role.participant_set_id

        if location_set_id != event.location_set_id:
            return

        if participant_set_id != event.participant_set_id:
            return

        deployment_id = event.deployment_id

        participants = Participant.query.filter_by(role_id=role.id)
        total_records = participants.count()
        processed_records = 0
        error_records = 0
        warning_records = 0
        error_log = []

        for participant in participants:
            if not participant.location_id:
                error_records += 1
                error_log.append(
                    {
                        "label": "ERROR",
                        "message": _("Participant ID %(part_id)s has no location", part_id=participant.participant_id),
                    }
                )
                continue

            if location_type.id == participant.location.location_type.id:
                location = participant.location
            else:
                try:
                    location = next(
                        a for a in participant.location.ancestors() if a.location_type.id == location_type.id
                    )
                    if not location:
                        error_records = total_records - processed_records
                        if task:
                            task.update_state(
                                state="PROGRESS",
                                meta={
                                    "total_records": total_records,
                                    "processed_records": processed_records,
                                    "error_records": error_records,
                                    "warning_records": warning_records,
                                    "error_log": error_log,
                                },
                            )
                        return
                except StopIteration:
                    error_records = total_records - processed_records
                    if task:
                        task.update_state(
                            state="PROGRESS",
                            meta={
                                "total_records": total_records,
                                "processed_records": processed_records,
                                "error_records": error_records,
                                "warning_records": warning_records,
                                "error_log": error_log,
                            },
                        )
                    return

            obs_submission = cls.query.filter_by(
                form_id=form.id,
                participant_id=participant.id,
                location_id=location.id,
                deployment_id=deployment_id,
                event_id=event.id,
                submission_type="O",
            ).first()

            if not obs_submission:
                obs_submission = cls(
                    form_id=form.id,
                    participant_id=participant.id,
                    location_id=location.id,
                    deployment_id=deployment_id,
                    event_id=event.id,
                    submission_type="O",
                    data={},
                )
                obs_submission.save()

            master_submission = cls.query.filter_by(
                form_id=form.id,
                participant_id=None,
                location_id=location.id,
                deployment_id=deployment_id,
                event_id=event.id,
                submission_type="M",
            ).first()

            if not master_submission:
                master_submission = cls(
                    form_id=form.id,
                    participant_id=None,
                    location_id=location.id,
                    deployment_id=deployment_id,
                    event_id=event.id,
                    submission_type="M",
                    data={},
                )
                master_submission.save()

            processed_records += 1
            if task:
                task.update_state(
                    state="PROGRESS",
                    meta={
                        "total_records": total_records,
                        "processed_records": processed_records,
                        "error_records": error_records,
                        "warning_records": warning_records,
                        "error_log": error_log,
                    },
                )

    def update_group_timestamps(self, data: dict) -> None:
        # local to avoid circular import
        from apollo.frontend.helpers import DictDiffer

        form = self.form
        form._populate_group_cache()
        group_names = form._group_cache.keys()
        original_data = (self.data or {}).copy()
        diff = DictDiffer(data, original_data)
        modified_tags = diff.added().union(diff.removed()).union(diff.changed())
        extra_data = (self.extra_data or {}).copy()
        group_timestamps = extra_data.get("group_timestamps", {})

        modified_timestamp = current_timestamp()
        for group_name in group_names:
            common_tags = modified_tags.intersection(form.get_group_tags(group_name))
            if common_tags:
                group_timestamps[group_name] = modified_timestamp.isoformat()

        extra_data["group_timestamps"] = group_timestamps
        self.extra_data = extra_data

    def update_related(self, data):
        """Update related objects.

        Given a dict used to update the submission,
        update the master with the data not in conflict,
        and update all related submissions with the
        conflict data
        """
        if self.form.form_type == "INCIDENT":
            return

        if self.form.untrack_data_conflicts:
            return

        combined_data = self.data
        combined_data.update(data)

        if self.quarantine_status == "A":
            conflict_tags = []
            subset = {}
        elif self.quarantine_status == "R":
            conflict_tags = self.compute_conflict_tags(set(combined_data.keys()).difference(set(self.form.vote_tags)))
            subset = {k: v for k, v in combined_data.items() if k not in conflict_tags and k not in self.form.vote_tags}
        else:
            conflict_tags = self.compute_conflict_tags(combined_data.keys())
            subset = {k: v for k, v in combined_data.items() if k not in conflict_tags}

        subset_keys = set(subset.keys())

        master = self.master

        siblings = self.siblings
        self.conflicts = trim_conflicts(self, conflict_tags, combined_data.keys())
        master.conflicts = trim_conflicts(master, conflict_tags, combined_data.keys())
        for sibling in siblings:
            sibling_data_keys = set(sibling.data.keys())

            if sibling.quarantine_status == "A":
                conflict_tags = []
            elif sibling.quarantine_status == "R":
                conflict_tags = sibling.compute_conflict_tags(
                    set(combined_data.keys()).difference(set(self.form.vote_tags))
                )
                subset.update(
                    {
                        k: sibling.data[k]
                        for k in sibling_data_keys.difference(subset_keys)
                        if k not in conflict_tags and k not in self.form.vote_tags
                    }
                )
            else:
                if self.quarantine_status == "R":
                    conflict_tags = sibling.compute_conflict_tags(
                        set(combined_data.keys()).difference(set(self.form.vote_tags))
                    )
                else:
                    conflict_tags = sibling.compute_conflict_tags(combined_data.keys())

                subset.update(
                    {k: sibling.data[k] for k in sibling_data_keys.difference(subset_keys) if k not in conflict_tags}
                )

            sibling.conflicts = trim_conflicts(sibling, conflict_tags, combined_data.keys())

        for key in master.overridden_fields:
            if key in master.data:
                subset[key] = master.data[key]
            else:
                subset.pop(key, None)

        master.update_group_timestamps(subset)
        master.data = subset
        master.participant_updated = self.participant_updated

        # update the 'voting_timestamp' extra data attribute only if
        # it has not been previously set and that it was defined in the
        # submission
        if not (master.extra_data or {}).get("voting_timestamp") and (self.extra_data or {}).get("voting_timestamp"):
            extra_data = master.extra_data or {}
            extra_data["voting_timestamp"] = self.extra_data.get("voting_timestamp")
            master.extra_data = extra_data

        db.session.begin(nested=True)
        db.session.add_all([self, master])
        db.session.add_all(siblings)
        db.session.commit()

    def update_master_offline_status(self):
        if self.master is None:
            return

        siblings = self.siblings
        master_offline_status = self.master.unreachable

        if siblings:
            if all(s.unreachable for s in self.siblings) and self.unreachable:
                self.master.unreachable = True
            else:
                self.master.unreachable = False
        else:
            self.master.unreachable = self.unreachable

        # if the offline status changed in any way
        if master_offline_status != self.master.unreachable:
            db.session.add(self.master)

    def compute_conflict_tags(self, tags=None):
        # don't compute if the 'track conflicts' flag is not set
        # on the form
        if self.form.untrack_data_conflicts:
            return []

        # or if the form is an incident form
        if self.form.form_type == "INCIDENT":
            return []

        # check only a subset of the tags
        tags_to_check = set(self.form.tags) - set(self.overridden_fields)
        if tags:
            tags_to_check = tags_to_check.intersection(set(tags))

        tags_to_check_non_votes = tags_to_check.difference(set(self.form.vote_tags))

        # conflict query
        any_conflict_query = [
            sa.func.bool_or(
                sa.and_(
                    Submission.data.has_key(tag),
                    sa.not_(Submission.data.contains({tag: self.data[tag]})),
                )
            ).label(tag)
            for tag in tags_to_check
            if tag in self.data
        ]
        non_vote_conflict_query = [
            sa.func.bool_or(
                sa.and_(
                    Submission.data.has_key(tag),
                    sa.not_(Submission.data.contains({tag: self.data[tag]})),
                )
            ).label(tag)
            for tag in tags_to_check_non_votes
            if tag in self.data
        ]

        if not any_conflict_query:
            return []
        siblings_no_quarantine = self.__siblings().filter(Submission.quarantine_status == "")
        siblings_with_results_quarantine = self.__siblings().filter(Submission.quarantine_status == "R")

        results_conflict = siblings_no_quarantine.with_entities(*any_conflict_query)
        results_vote_conflict = siblings_with_results_quarantine.with_entities(*non_vote_conflict_query)

        any_conflict = {k for result in results_conflict for k, v in result._asdict().items() if v}
        vote_conflict = {k for result in results_vote_conflict for k, v in result._asdict().items() if v}

        return any_conflict.union(vote_conflict)

    def get_incident_status_display(self):
        d = dict(self.INCIDENT_STATUSES)
        return d.get(self.incident_status, _("Unmarked"))

    def _compute_completion(self, group_tags):
        are_empty_values = (
            [
                # TODO: check the empty values
                self.data.get(tag) not in (None, "", [])
                for tag in group_tags
            ]
            if self.data
            else []
        )
        if are_empty_values and all(are_empty_values):
            return "Complete"
        elif any(are_empty_values):
            return "Partial"
        else:
            return "Missing"

    def completion(self, group_name):
        group_tags = self.form.get_group_tags(group_name)
        if self.form.form_type == "INCIDENT" or self.form.untrack_data_conflicts:
            return self._compute_completion(group_tags)
        else:
            conflict_tags = set(group_tags).intersection(set(self.conflicts or []))
            if conflict_tags:
                return "Conflict"
            return self._compute_completion(group_tags)

    def __siblings(self):
        """Returns siblings as a SQLA query object."""
        return Submission.query.filter(
            Submission.deployment_id == self.deployment_id,
            Submission.event_id == self.event_id,
            Submission.form_id == self.form_id,
            Submission.serial_no == self.serial_no,
            Submission.location_id == self.location_id,
            Submission.submission_type == "O",
            Submission.id != self.id,
        )

    def __master(self):
        return Submission.query.filter(
            Submission.deployment_id == self.deployment_id,
            Submission.event_id == self.event_id,
            Submission.form_id == self.form_id,
            Submission.serial_no == self.serial_no,
            Submission.location_id == self.location_id,
            Submission.submission_type == "M",
        ).first()

    @property
    def siblings(self):
        """Returns siblings as POPOs."""
        if not hasattr(self, "_siblings"):
            self._siblings = self.__siblings().all()

        return self._siblings

    @property
    def master(self):
        if self.submission_type == "M":
            return self

        if self.form.form_type == "INCIDENT":
            self._master = None

        if not hasattr(self, "_master"):
            self._master = Submission.query.filter(
                Submission.deployment_id == self.deployment_id,
                Submission.event_id == self.event_id,
                Submission.form_id == self.form_id,
                Submission.location_id == self.location_id,
                Submission.submission_type == "M",
            ).first()

        return self._master

    def has_image_data(self):
        return any(self.data.get(tag) for tag in self.form.get_image_fields())

    def get_result_image_count(self):
        return sum([bool(self.data.get(tag)) for tag in self.form.result_images or []])

    def get_image_data_fields(self):
        return {
            self.data.get(tag): self.form.get_field_by_tag(tag)
            for tag in self.form.get_image_fields()
            if self.data.get(tag)
        }

    def get_image_data(self):
        image_tags = self.form.get_image_fields()
        descriptions = [self.form.get_field_by_tag(tag).get("description") for tag in image_tags]
        attachments = [
            SubmissionImageAttachment.query.filter_by(uuid=self.data.get(tag)).first() if self.data.get(tag) else None
            for tag in image_tags
        ]

        image_data = [
            {"tag": tag, "description": description, "attachment": attachment}
            for (tag, description, attachment) in zip(image_tags, descriptions, attachments)
        ]

        return image_data

    def delete_image_attachment(self, tag):
        if not self.data.get(tag):
            return False

        attachment = SubmissionImageAttachment.query.filter_by(uuid=self.data.get(tag)).first()

        if not attachment:
            return False

        data = self.data.copy()
        data.pop(tag)
        self.update_group_timestamps(data)
        extra_data = self.extra_data.copy()
        self.__class__.query.filter_by(id=self.id).update(
            {
                "data": data,
                "extra_data": extra_data,
            }
        )
        db.session.delete(attachment)
        db.session.commit()

        return True


class SubmissionComment(BaseModel):
    __tablename__ = "submission_comment"

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey("submission.id", ondelete="CASCADE"), nullable=False)
    submission = db.relationship(
        "Submission", backref=db.backref("comments", cascade="all, delete", passive_deletes=True)
    )
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User", backref="submission_comments")
    comment = db.Column(db.String)
    submit_date = db.Column(db.DateTime, default=current_timestamp)
    deployment_id = db.Column(db.Integer, db.ForeignKey("deployment.id", ondelete="CASCADE"), nullable=False)
    deployment = db.relationship(
        "Deployment", backref=db.backref("submission_comments", cascade="all, delete", passive_deletes=True)
    )


class SubmissionVersion(BaseModel):
    __tablename__ = "submission_version"

    CHANNEL_CHOICES = (
        ("SMS", _("SMS")),
        ("WEB", _("Web")),
        ("API", _("API")),
        ("ODK", _("ODK")),
        ("PWA", _("PWA")),
    )
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey("submission.id", ondelete="CASCADE"), nullable=False)
    data = db.Column(JSONB)
    submission = db.relationship(
        "Submission", backref=db.backref("versions", cascade="all, delete", passive_deletes=True)
    )
    timestamp = db.Column(db.DateTime, default=current_timestamp)
    channel = db.Column(ChoiceType(CHANNEL_CHOICES))
    deployment_id = db.Column(db.Integer, db.ForeignKey("deployment.id", ondelete="CASCADE"), nullable=False)
    deployment = db.relationship(
        "Deployment", backref=db.backref("submission_versions", cascade="all, delete", passive_deletes=True)
    )
    identity = db.Column(db.String, default="unknown", nullable=False)

    def changes(self):
        from apollo import models

        added = []
        changed = []
        deleted = []

        attr_current = set(self.data.keys())

        prev_changeset = (
            models.SubmissionVersion.query.filter(
                models.SubmissionVersion.submission == self.submission,  # noqa
                models.SubmissionVersion.timestamp < self.timestamp,  # noqa
            )
            .order_by(sa.desc(models.SubmissionVersion.timestamp))
            .first()
        )

        if prev_changeset:
            attr_previous = set(prev_changeset.data.keys())

            added = attr_current.difference(attr_previous)
            deleted = attr_previous.difference(attr_current)
            changed = {
                attr
                for attr in attr_current.intersection(attr_previous)
                if self.data[attr] != prev_changeset.data[attr]
            }
        else:
            added = set(self.data.keys())

        return {"added": added, "deleted": deleted, "changed": changed}


class SubmissionImageAttachment(BaseModel):
    __tablename__ = "image_attachment"

    id = db.Column(db.Integer, nullable=False, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey("submission.id", ondelete="CASCADE"), nullable=False)
    photo = db.Column(UploadedFileField(upload_storage="images", upload_type=UploadedImageWithThumb))

    submission = db.relationship(
        "Submission", backref=db.backref("image_attachments", cascade="all, delete", passive_deletes=True)
    )


def trim_conflicts(submission, conflict_tags, data_keys):
    """Trim resolved conflicts.

    Remove keys that were updated and no longer in conflict
    and add keys that are new conflicts
    """
    conflict_keys = set(conflict_tags)

    # these were updated, they are not in conflict any longer
    updated_unconflicted_keys = set(data_keys) - set(conflict_tags)
    new_conflicts = set(submission.conflicts) - updated_unconflicted_keys if submission.conflicts else set()

    return sorted(new_conflicts.union(conflict_keys))
