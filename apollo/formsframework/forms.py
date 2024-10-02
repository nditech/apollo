# -*- coding: utf-8 -*-
import math
import re
from datetime import datetime
from functools import partial

import wtforms
from flask import g
from flask_babel import gettext as _
from flask_wtf import FlaskForm as SecureForm
from flask_wtf.file import FileField
from wtforms_alchemy.fields import QuerySelectMultipleField
from wtforms_alchemy.utils import choice_type_coerce_factory

from .. import services
from ..core import db
from ..deployments.models import Event
from ..formsframework.models import Form
from ..frontend.helpers import DictDiffer
from ..participants.models import Participant, PhoneContact
from ..submissions.models import Submission, SubmissionComment, SubmissionVersion
from ..utils import current_timestamp
from .custom_fields import IntegerSplitterField

ugly_phone = re.compile("[^0-9]*")


def update_submission_version(submission):
    """Version control for submissions."""
    # save actual version data
    data_fields = submission.form.tags
    version_data = {k: submission.data.get(k) for k in data_fields if k in submission.data}

    if submission.form.form_type == "INCIDENT":
        if submission.incident_status:
            version_data["status"] = submission.incident_status.code

        if submission.incident_description:
            version_data["description"] = submission.incident_description

    # get previous version
    previous = (
        SubmissionVersion.query.filter(SubmissionVersion.submission == submission)
        .order_by(SubmissionVersion.timestamp.desc())
        .first()
    )

    if previous:
        diff = DictDiffer(version_data, previous.data)

        # don't do anything if the data wasn't changed
        if not diff.added() and not diff.removed() and not diff.changed():
            return

    channel = "SMS"
    identity = g.phone

    services.submission_versions.create(
        submission_id=submission.id,
        data=version_data,
        timestamp=datetime.utcnow(),
        channel=channel,
        identity=identity,
        deployment_id=submission.deployment_id,
    )


def filter_participants(form, participant_id):
    """Returns a valid participant from the current event and selected form."""
    if not form:
        return None
    event = getattr(g, "event", services.events.default())
    current_events = services.events.overlapping_events(event)
    form_events = Event.query.filter(Event.forms.contains(form))
    query = (
        current_events.intersect(form_events)
        .join(
            Participant,
            Participant.participant_set_id == Event.participant_set_id,  # noqa
        )
        .with_entities(Participant)
    )

    participant = query.filter_by(participant_id=participant_id).first()

    return participant


def filter_form(form_id):
    """Retrieves a form if it is active in the current event."""
    event = getattr(g, "event", services.events.default())
    current_events = services.events.overlapping_events(event)
    query = current_events.join(Event.forms).with_entities(Form)

    if form_id:
        form = query.filter_by(id=form_id).first()

        return form


def find_active_forms():
    """Retrieves all currently active forms."""
    event = getattr(g, "event", services.events.default())
    current_events = services.events.overlapping_events(event)
    query = current_events.join(Event.forms).with_entities(Form)

    return query


class NullValueValidator:
    def __init__(self, min=None, max=None, message=None, null_value=None):
        """Initializer."""
        self.max = max
        self.min = min
        self.null_value = null_value
        self.message = message
        self.field_flags = {}
        if self.max is not None:
            self.field_flags["max"] = self.max
        if self.min is not None:
            self.field_flags["min"] = self.min
        if self.null_value is not None:
            self.field_flags["null_value"] = self.null_value

    def value_is_null(self, value):
        return self.null_value is not None and value == self.null_value

    def __call__(self, form, field):
        data = field.data
        if (
            data is not None
            and not math.isnan(data)
            and (self.min is None or data >= self.min)
            and (
                self.max is None or self.value_is_null(data) or data <= self.max  # noqa
            )
        ):
            return

        if self.message is not None:
            message = self.message

        # we use %(min)s interpolation to support floats, None, and
        # Decimals without throwing a formatting exception.
        elif self.max is None:
            message = field.gettext("Number must be at least %(min)s.")

        elif self.min is None:
            message = field.gettext("Number must be at most %(max)s.")

        else:
            message = field.gettext("Number must be between %(min)s and %(max)s.")

        raise wtforms.validators.ValidationError(message % {"min": self.min, "max": self.max})


class BaseQuestionnaireForm(wtforms.Form):
    form = wtforms.StringField(
        "Form", validators=[wtforms.validators.data_required()], filters=[lambda data: filter_form(data)]
    )
    form_serial = wtforms.StringField("Form Serial", validators=[wtforms.validators.optional()])
    sender = wtforms.StringField("Sender", validators=[wtforms.validators.data_required()])
    comment = wtforms.StringField("Comment", validators=[wtforms.validators.optional()])

    def process(self, formdata=None, obj=None, **kwargs):
        self._formdata = formdata
        return super(BaseQuestionnaireForm, self).process(formdata, obj, **kwargs)

    def validate(self, *args, **kwargs):
        success = super(BaseQuestionnaireForm, self).validate(*args, **kwargs)
        if success and self._formdata:
            unknown_fields = [f for f in list(self._formdata.keys()) if f not in list(self._fields.keys())]
            if unknown_fields:
                if type(self._errors) is dict:
                    self._errors.update({"__all__": unknown_fields})
                else:
                    self._errors = {"__all__": unknown_fields}

                success = False

        return success

    def save(self, commit=True):
        ignored_fields = ["form", "participant", "sender", "comment"]
        submission = None
        current_events = services.events.overlapping_events(g.event)
        current_event_ids = current_events.with_entities(Event.id)
        update_params = {}

        # also ignore fields that have errors so as not to save them
        ignored_fields.extend(self.errors.keys())
        form = self.data.get("form")
        participant = self.data.get("participant")
        form_serial = self.data.get("form_serial")

        if form.form_type == "CHECKLIST":
            # when searching for the submission, take into cognisance
            # that the submission may be in one of several concurrent
            # events
            submission = Submission.query.filter(
                Submission.participant == participant,
                Submission.form == form,
                Submission.submission_type == "O",
                Submission.event_id.in_(current_event_ids),
            ).first()

            if self.data.get("comment") and submission and commit:
                SubmissionComment.create(
                    submission=submission, comment=self.data.get("comment"), deployment=submission.deployment
                )
        elif form.form_type == "SURVEY":
            submission = Submission.query.filter(
                Submission.participant == participant,
                Submission.form == form,
                Submission.submission_type == "O",
                Submission.serial_no == form_serial,
                Submission.event_id.in_(current_event_ids),
            ).first()

            if self.data.get("comment") and submission and commit:
                SubmissionComment.create(
                    submission=submission, comment=self.data.get("comment"), deployment=submission.deployment
                )
        else:
            # the submission event is determined by taking the intersection
            # of form events, participant events and concurrent events
            # and taking the last event ordered by descending end date
            event = (
                current_events.join(Event.forms)
                .filter(Event.forms.contains(form), Event.participant_set_id == participant.participant_set_id)
                .order_by(Event.end.desc())
                .first()
            )

            submission = Submission(
                submission_type="O",
                form=form,
                participant=participant,
                location=participant.location,
                created=current_timestamp(),
                event=event,
                deployment_id=event.deployment_id,
            )
            if self.data.get("comment"):
                submission.incident_description = self.data.get("comment")

        if submission:
            data = submission.data.copy() if submission.data else {}
            form_fields = [f for f in self.data.keys() if f not in ignored_fields]

            changed_fields = []
            for form_field in form_fields:
                field_data = self.data.get(form_field)

                if isinstance(field_data, int):
                    if data.get(form_field) != field_data:
                        changed_fields.append(form_field)
                        data[form_field] = field_data
                        continue

                if isinstance(field_data, list) and field_data:
                    original_value = data.get(form_field)
                    if isinstance(original_value, list):
                        original_value = sorted(original_value)
                    if original_value != field_data:
                        changed_fields.append(form_field)
                        data[form_field] = field_data
                    continue

                if isinstance(field_data, str) and field_data:
                    if data.get(form_field) != field_data:
                        changed_fields.append(form_field)
                        data[form_field] = field_data

            if changed_fields:
                phone_num = ugly_phone.sub("", self.data.get("sender"))
                g.phone = phone_num

                # confirm if phone number is known and verified
                participant = self.data.get("participant")

                # retrieve the first phone contact that matches
                phone_contact = services.phone_contacts.lookup(phone_num, participant)

                if phone_contact:
                    submission.sender_verified = phone_contact.verified

                    if commit:
                        phone_contact.touch()
                        phone_contact.save()
                else:
                    if submission.id is None:
                        submission.sender_verified = False
                    else:
                        update_params["sender_verified"] = False

                    phone = services.phone_contacts.lookup(phone_num, participant)
                    if not phone:
                        phone_contact = PhoneContact(number=phone_num, participant_id=participant.id)

                    if commit:
                        phone_contact.touch()
                        phone_contact.save()

                if commit:
                    if submission.id is None:
                        # for a fresh submission, everything will get saved
                        submission.update_group_timestamps(data)
                        submission.data = data
                        submission.last_phone_number = phone_num
                        submission.participant_updated = current_timestamp()
                        submission.save()
                    else:
                        # for an existing submission, we need an update,
                        # otherwise the JSONB field won't get persisted
                        update_params["data"] = data
                        update_params["last_phone_number"] = phone_num
                        update_params["participant_updated"] = current_timestamp()  # noqa
                        submission.update_group_timestamps(data)
                        extra_data = submission.extra_data or {}
                        now = current_timestamp().isoformat()

                        # set the 'voting_timestamp' extra data attribute to
                        # the current timestamp only if a voting share was
                        # updated and it has not been previously set
                        if (
                            any(vs in data.keys() for vs in submission.form.vote_shares)  # noqa
                            and not (submission.extra_data or {}).get("voting_timestamp")  # noqa
                        ):
                            extra_data["voting_timestamp"] = now  # noqa

                        # set the 'turnout_timestamps' attribute for any of the
                        # turnout fields if they have been reported for the
                        # first time
                        turnout_fields = set(data.keys()).intersection(set(submission.form.turnout_fields or []))  # noqa
                        if turnout_fields:
                            if not extra_data.get("turnout_timestamps"):
                                extra_data["turnout_timestamps"] = {}

                            for turnout_field in turnout_fields:
                                if not extra_data["turnout_timestamps"].get(turnout_field):  # noqa
                                    extra_data["turnout_timestamps"][turnout_field] = now  # noqa

                        if extra_data:
                            update_params["extra_data"] = extra_data

                        services.submissions.find(id=submission.id).update(update_params, synchronize_session=False)
                        db.session.refresh(submission)

                    # if data was changed, update conflict marker,
                    # update location data and create a new version
                    if changed_fields:
                        submission.update_related(data)
                        update_submission_version(submission)

        return submission


def build_questionnaire(form, data=None):
    """Builds a questionnaire for use in text parsing."""
    fields = {"groups": []}
    fields["participant"] = wtforms.StringField(
        "Participant", filters=[partial(filter_participants, form)], validators=[wtforms.validators.data_required()]
    )

    for group in form.data["groups"]:
        groupspec = (group["name"], [])

        for field in group["fields"]:
            # if the field has options, create a list of choices
            field_type = field.get("type")
            if field_type in ("select", "multiselect", "category"):
                choices = [(v, k) for k, v in field.get("options").items()]

                if field["type"] == "multiselect":
                    fields[field["tag"]] = IntegerSplitterField(
                        field["tag"],
                        choices=choices,
                        description=field["description"],
                        validators=[wtforms.validators.optional()],
                    )
                else:
                    fields[field["tag"]] = wtforms.SelectField(
                        field["tag"],
                        choices=choices,
                        coerce=int,
                        description=field["description"],
                        validators=[wtforms.validators.optional()],
                        widget=wtforms.widgets.TextInput(),
                    )
            elif field_type in ("comment", "string"):
                fields[field["tag"]] = wtforms.StringField(
                    field["tag"], description=field["description"], validators=[wtforms.validators.optional()]
                )
            elif field_type in ("boolean", "integer"):
                if field_type == "boolean":
                    field_validators = [wtforms.validators.optional()]
                else:
                    field_validators = [
                        wtforms.validators.optional(),
                        NullValueValidator(
                            min=field.get("min", 0),
                            max=field.get("max", 9999),
                            null_value=field.get("null_value"),
                        ),
                    ]

                fields[field["tag"]] = wtforms.IntegerField(
                    field["tag"], description=field["description"], validators=field_validators
                )

        fields["groups"].append(groupspec)

    form_class = type("QuestionnaireForm", (BaseQuestionnaireForm,), fields)

    return form_class(data)


class FormForm(SecureForm):
    name = wtforms.StringField(_("Name"), validators=[wtforms.validators.DataRequired()])
    prefix = wtforms.StringField(
        _("Form Code"),
        validators=[wtforms.validators.DataRequired()],
        description=_("What code to identify this form in text messages."),
    )
    form_type = wtforms.SelectField(
        _("Form Type"),
        choices=Form.FORM_TYPES,
        coerce=choice_type_coerce_factory(Form.form_type.type),
        validators=[wtforms.validators.DataRequired()],
    )
    untrack_data_conflicts = wtforms.BooleanField(
        _("Don't Track Data Conflicts"),
        description=_("Whether data conflicts between observers in the same location are tracked or not."),
    )  # noqa
    calculate_moe = wtforms.BooleanField(
        _("Calculate MOE"), description=_("Whether to display margin of error calculations or not.")
    )  # noqa
    quality_checks_enabled = wtforms.BooleanField(
        _("QA Enabled"), description=_("Whether to enable quality assurance or not.")
    )
    show_map = wtforms.BooleanField(
        _("Show Map View"), description=_("Whether to display the map view for submissions or not.")
    )  # noqa
    show_moment = wtforms.BooleanField(
        _("Show Timestamp Column"),
        description=_("Enabling this option will show the date and time for the submission in the list view."),
    )  # noqa
    show_progress = wtforms.BooleanField(
        _("Show Daily Progress"),
        description=_("Enabling this option will show the daily progress for this form on the dashboard."),
    )  # noqa
    accredited_voters_tag = wtforms.SelectField(_("Accredited Voters Field"), choices=[("", "")])
    blank_votes_tag = wtforms.SelectField(_("Blank Votes Field"), choices=[("", "")])
    invalid_votes_tag = wtforms.SelectField(_("Invalid Votes Field"), choices=[("", "")])
    registered_voters_tag = wtforms.SelectField(_("Registered Voters Field"), choices=[("", "")])
    vote_shares = wtforms.SelectMultipleField(
        _("Vote Shares"), description=_("Questions representing election results.")
    )  # noqa
    turnout_fields = wtforms.SelectMultipleField(
        _("Partial Turnout Fields"), description=_("Fields representing turnout values.")
    )  # noqa
    turnout_registered_voters_tag = wtforms.SelectField(
        _("Partial Turnout Registered Voters Field"), choices=[("", "")]
    )  # noqa
    result_images = wtforms.SelectMultipleField(
        _("Result Images"),
        description=_("Questions representing election result images."),  # noqa
    )


class FormImportForm(SecureForm):
    import_file = FileField(_("Import file"))


def make_questionnaire_hidden_toggle_form(deployment):
    """Questionnaire with support for hidden forms."""

    def _get_forms():
        return Form.query.filter(Form.deployment == deployment).all()

    class QuestionnaireHiddenToggleForm(SecureForm):
        forms = QuerySelectMultipleField(
            query_factory=_get_forms,
            option_widget=wtforms.widgets.CheckboxInput(),
            widget=wtforms.widgets.ListWidget(prefix_label=False),
            get_pk=lambda f: f.id,
        )
        mode = wtforms.HiddenField(
            validators=[
                wtforms.validators.AnyOf(["hide", "show"]),
                wtforms.validators.InputRequired(),
            ]
        )

    return QuestionnaireHiddenToggleForm()
