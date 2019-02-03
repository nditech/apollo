# -*- coding: utf-8 -*-
from datetime import datetime
from functools import partial
import re

from flask import g
from flask_babelex import lazy_gettext as _
from flask_wtf import FlaskForm as SecureForm
from flask_wtf.file import FileField
from wtforms import (
    Form, BooleanField, IntegerField, SelectField, StringField, validators,
    widgets)
from wtforms_alchemy.utils import choice_type_coerce_factory

from .. import models, services, utils
from ..frontend.helpers import DictDiffer
from .custom_fields import IntegerSplitterField

ugly_phone = re.compile('[^0-9]*')


def update_submission_version(submission):
    # save actual version data
    data_fields = submission.form.tags
    version_data = {
        k: submission.data.get(k)
        for k in data_fields if k in submission.data}

    if submission.form.form_type == 'INCIDENT':
        version_data['status'] = submission.incident_status.code
        version_data['description'] = submission.incident_description

    # get previous version
    previous = services.submission_versions.find(
        submission=submission).order_by(
            models.SubmissionVersion.timestamp.desc()).first()

    if previous:
        diff = DictDiffer(version_data, previous.data)

        # don't do anything if the data wasn't changed
        if not diff.added() and not diff.removed() and not diff.changed():
            return

    channel = 'SMS'
    identity = g.phone

    services.submission_versions.create(
        submission_id=submission.id,
        data=version_data,
        timestamp=datetime.utcnow(),
        channel=channel,
        identity=identity,
        deployment_id=submission.deployment_id
    )


def filter_participants(form, participant_id):
    if not form:
        return None
    event = getattr(g, 'event', services.events.default())
    current_events = services.events.overlapping_events(event)
    form_events = models.Event.query.filter_by(form_set=form.form_set)
    query = current_events.intersect(form_events).join(
        models.Participant,
        models.Participant.participant_set_id == models.Event.participant_set_id    # noqa
    ).with_entities(models.Participant)

    participant = query.filter_by(participant_id=participant_id).first()

    return participant


def filter_form(form_id):
    event = getattr(g, 'event', services.events.default())
    current_events = services.events.overlapping_events(event)
    query = current_events.join(
        models.Form,
        models.Event.form_set_id == models.Form.form_set_id
    ).with_entities(models.Form)

    if form_id:
        form = query.filter_by(id=form_id).first()

        return form


def find_active_forms():
    event = getattr(g, 'event', services.events.default())
    current_events = services.events.overlapping_events(event)
    query = current_events.join(
        models.Form,
        models.Event.form_set_id == models.Form.form_set_id
    ).with_entities(models.Form)

    return query


class BaseQuestionnaireForm(Form):
    form = StringField(
        'Form', validators=[validators.required()],
        filters=[lambda data: filter_form(data)])
    sender = StringField('Sender', validators=[validators.required()])
    comment = StringField('Comment', validators=[validators.optional()])

    def process(self, formdata=None, obj=None, **kwargs):
        self._formdata = formdata
        return super(BaseQuestionnaireForm, self).process(
            formdata, obj, **kwargs)

    def validate(self, *args, **kwargs):
        success = super(BaseQuestionnaireForm, self).validate(*args, **kwargs)
        if success and self._formdata:
            unknown_fields = [
                f for f in list(self._formdata.keys())
                if f not in list(self._fields.keys())
            ]
            if unknown_fields:
                if type(self._errors) == dict:
                    self._errors.update({'__all__': unknown_fields})
                else:
                    self._errors = {'__all__': unknown_fields}

                success = False

        return success

    def save(self, commit=True):
        ignored_fields = ['form', 'participant', 'sender', 'comment']
        submission = None
        current_events = services.events.overlapping_events(
            g.event)
        current_event_ids = current_events.with_entities(models.Event.id)
        update_params = {}

        # also ignore fields that have errors so as not to save them
        ignored_fields.extend(self.errors.keys())
        try:
            form = self.data.get('form')
            participant = self.data.get('participant')

            if form.form_type == 'CHECKLIST':
                # when searching for the submission, take into cognisance
                # that the submission may be in one of several concurrent
                # events
                submission = models.Submission.query.filter(
                    models.Submission.participant == participant,
                    models.Submission.form == form,
                    models.Submission.submission_type == 'O',
                    models.Submission.event_id.in_(current_event_ids)
                ).first()

                if self.data.get('comment') and submission and commit:
                    services.submission_comments.create_comment(
                        submission, self.data.get('comment'))
            else:
                # the submission event is determined by taking the intersection
                # of form events, participant events and concurrent events
                # and taking the last event ordered by descending end date
                event = current_events.filter_by(
                    form_set_id=form.form_set_id,
                    participant_set_id=participant.participant_set_id
                ).order_by(models.Event.end.desc()).first()

                submission = models.Submission(
                    submission_type='O',
                    form=form,
                    participant=participant,
                    location=participant.location,
                    created=utils.current_timestamp(),
                    event=event,
                    deployment_id=event.deployment_id)
                if self.data.get('comment'):
                    submission.incident_description = self.data.get('comment')

            if submission:
                data = submission.data.copy() if submission.data else {}
                form_fields = [
                    f for f in self.data.keys() if f not in ignored_fields
                ]

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
                        if (original_value != field_data):
                            changed_fields.append(form_field)
                            data[form_field] = field_data
                        continue

                    if isinstance(field_data, str) and field_data:
                        if data.get(form_field) != field_data:
                            changed_fields.append(form_field)
                            data[form_field] = field_data

                if changed_fields:
                    phone_num = ugly_phone.sub('', self.data.get('sender'))
                    g.phone = phone_num

                    # confirm if phone number is known and verified
                    participant = self.data.get('participant')

                    # retrieve the first phone contact that matches
                    phone_contact = services.participant_phones.lookup(
                        phone_num, participant)

                    if phone_contact:
                        submission.sender_verified = phone_contact.verified
                        phone_contact.last_seen = utils.current_timestamp()

                        if commit:
                            phone_contact.save()
                    else:
                        if submission.id is None:
                            submission.sender_verified = False
                        else:
                            update_params['sender_verified'] = False

                        phone = services.phones.get_by_number(phone_num)
                        if not phone:
                            phone = models.Phone(number=phone_num)

                        phone_contact = models.ParticipantPhone(
                            phone=phone, participant_id=participant.id,
                            verified=False)

                        if commit:
                            phone.save()
                            phone_contact.save()

                    if commit:
                        submission.data = data
                        if submission.id is None:
                            # for a fresh submission, everything will get saved
                            submission.save()
                        else:
                            # for an existing submission, we need an update,
                            # otherwise the JSONB field won't get persisted
                            update_params['data'] = data
                            services.submissions.find(
                                id=submission.id
                            ).update(update_params, synchronize_session=False)

                        # update conflict markers and master data
                        changed_subset = {
                            k: v for k, v in data.items()
                            if k in changed_fields
                        }
                        if changed_subset:
                            submission.update_related(changed_subset)
                        update_submission_version(submission)

                    # update completion rating for participant
                    # if submission.form.form_type == 'CHECKLIST':
                    #     update_participant_completion_rating(participant)
        except Exception:
            pass

        return submission


def build_questionnaire(form, data=None):
    fields = {'groups': []}
    fields['participant'] = StringField(
        'Participant',
        filters=[partial(filter_participants, form)],
        validators=[validators.required()])

    for group in form.data['groups']:
        groupspec = (group['name'], [])

        for field in group['fields']:
            # if the field has options, create a list of choices
            field_type = field.get('type')
            if field_type in ('select', 'multiselect', 'category'):
                choices = [(v, k) for k, v in field.get('options').items()]

                if field['type'] == 'multiselect':
                    fields[field['tag']] = IntegerSplitterField(
                        field['tag'],
                        choices=choices,
                        description=field['description'],
                        validators=[validators.optional()],
                    )
                else:
                    fields[field['tag']] = SelectField(
                        field['tag'],
                        choices=choices,
                        coerce=int,
                        description=field['description'],
                        validators=[validators.optional()],
                        widget=widgets.TextInput()
                    )
            elif field_type in ('comment', 'string'):
                fields[field['tag']] = StringField(
                    field['tag'], description=field['description'],
                    validators=[validators.optional()])
            elif field_type in ('boolean', 'integer'):
                if field_type == 'boolean':
                    field_validators = [validators.optional()]
                else:
                    field_validators = [
                        validators.optional(),
                        validators.NumberRange(min=field.get('min', 0),
                                               max=field.get('max', 9999))
                    ]

                fields[field['tag']] = IntegerField(
                    field['tag'],
                    description=field['description'],
                    validators=field_validators)

        fields['groups'].append(groupspec)

    form_class = type('QuestionnaireForm', (BaseQuestionnaireForm,), fields)

    return form_class(data)


class FormForm(SecureForm):
    name = StringField(_('Name'), validators=[validators.InputRequired()])
    prefix = StringField(_('Prefix'), validators=[validators.InputRequired()])
    form_type = SelectField(
        _('Form Type'), choices=models.Form.FORM_TYPES,
        coerce=choice_type_coerce_factory(
            models.Form.form_type.type),
        validators=[validators.InputRequired()])
    require_exclamation = BooleanField(_('Require Exclamation'))
    track_data_conflicts = BooleanField(_('Track Data Conflicts?'))
    calculate_moe = BooleanField(_('Calculate MOE'))
    quality_checks_enabled = BooleanField(_('QA Enabled'))
    accredited_voters_tag = StringField(_('Accredited Voters Field'))
    blank_votes_tag = StringField(_('Blank Votes Field'))
    invalid_votes_tag = StringField(_('Invalid Votes Field'))
    registered_votes_tag = StringField(_('Registered Voters Field'))


class FormImportForm(SecureForm):
    import_file = FileField(_('Import file'))
