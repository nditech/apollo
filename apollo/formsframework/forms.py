# -*- coding: utf-8 -*-
from datetime import datetime
from functools import partial

from wtforms import (
    Form, BooleanField, IntegerField, SelectField, StringField, validators,
    widgets)
from flask import g
from flask_babelex import lazy_gettext as _
from flask_wtf import FlaskForm as SecureForm
from .. import services, models
from ..frontend.helpers import DictDiffer
from ..participants.utils import update_participant_completion_rating
from .custom_fields import IntegerSplitterField
import json
import re

ugly_phone = re.compile('[^\d]*')


def update_submission_version(document):
    # save actual version data
    data_fields = document.form.tags
    if document.form.form_type == 'INCIDENT':
        data_fields.extend(['status'])
    version_data = {k: document[k] for k in data_fields if k in document}

    # get previous version
    previous = services.submission_versions.find(
        submission=document).order_by('-timestamp').first()

    if previous:
        prev_data = json.loads(previous.data)
        diff = DictDiffer(version_data, prev_data)

        # don't do anything if the data wasn't changed
        if not diff.added() and not diff.removed() and not diff.changed():
            return

    channel = 'SMS'

    services.submission_versions.create(
        submission=document,
        data=json.dumps(version_data),
        timestamp=datetime.utcnow(),
        channel=channel,
        identity=g.get('phone', '')
    )


def filter_participants(form, participant_id):
    if not form:
        return None
    event = getattr(g, 'event', services.events.default())
    current_events = services.events.overlapping_events(event)
    form_events = models.Event.query.filter_by(form_set=form.form_set)
    participant_sets = current_events.intersect(form_events).join(
        models.Event.participant_set).with_entities(models.ParticipantSet)

    participant = models.Participant.objects(
            event__in=events, participant_id=participant_id).first()

    return participant


def filter_form(form_pk):
    event = getattr(g, 'event', services.events.default())
    current_events = services.events.overlapping_events(event)

    if form_pk:
        form = models.Form.objects(events__in=events, pk=form_pk).first()

        return form


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
            unknown_fields = [f for f in list(self._formdata.keys()) if f not in list(self._fields.keys())]
            if unknown_fields:
                if type(self._errors) == dict:
                    self._errors.update({'__all__': unknown_fields})
                else:
                    self._errors = {'__all__': unknown_fields}

                success = False

        return success

    def save(self):
        ignored_fields = ['form', 'participant', 'sender', 'comment']
        submission = None

        # also ignore fields that have errors so as not to save them
        ignored_fields.extend(list(self.errors.keys()))
        try:
            participant = self.data.get('participant')

            if self.data.get('form').form_type == 'CHECKLIST':
                # when searching for the submission, take into cognisance
                # that the submission may be in one of several concurrent
                # events
                submission = models.Submission.objects(
                    contributor=participant,
                    form=self.data.get('form'), submission_type='O',
                    event__in=services.events.overlapping_events(g.event),
                    deployment=self.data.get('form').deployment).first()
                if self.data.get('comment') and submission:
                    services.submission_comments.create_comment(
                        submission, self.data.get('comment'))
            else:
                # the submission event is determined by taking the intersection
                # of form events and concurrent events and taking an arbitrary
                # element from that set; basic idea being that we want to
                # find what is common between the form's events and the current
                # events
                submission_event = participant.event
                submission = models.Submission(
                    form=self.data.get('form'),
                    contributor=self.data.get('participant'),
                    location=self.data.get('participant').location,
                    created=datetime.utcnow(),
                    deployment=submission_event.deployment,
                    event=submission_event)
                if self.data.get('comment'):
                    submission.description = self.data.get('comment')

            if submission:
                form_fields = [f for f in list(self.data.keys()) if f not in ignored_fields]
                change_detected = False
                for form_field in form_fields:
                    if isinstance(self.data.get(form_field), int):
                        change_detected = True
                        if (
                            getattr(submission, form_field, None) !=
                            self.data.get(form_field)
                        ):
                            setattr(
                                submission, form_field,
                                self.data.get(form_field))

                    if (
                        isinstance(self.data.get(form_field), list) and
                            self.data.get(form_field)
                    ):
                        change_detected = True
                        original_value = getattr(submission, form_field, None)
                        if isinstance(original_value, list):
                            original_value = sorted(original_value)
                        if (original_value != self.data.get(form_field)):
                            setattr(submission, form_field,
                                    self.data.get(form_field))

                if change_detected:
                    g.phone = self.data.get('sender')

                    # confirm if phone number is known and verified
                    participant = self.data.get('participant')

                    # retrieve the first phone contact that matches
                    phone_contact = next(filter(
                        lambda phone: ugly_phone.sub('', g.phone) ==
                        phone.number,
                        participant.phones), False)
                    if phone_contact:
                        submission.sender_verified = phone_contact.verified
                        phone_contact.last_seen = datetime.utcnow()
                        participant.save()
                    else:
                        submission.sender_verified = False
                        phone_contact = models.PhoneContact(
                            number=g.phone,
                            verified=False, last_seen=datetime.utcnow())
                        participant.update(add_to_set__phones=phone_contact)
 
                    submission.save()
                    update_submission_version(submission)

                    # update completion rating for participant
                    if submission.form.form_type == 'CHECKLIST':
                        update_participant_completion_rating(participant)
        except models.Submission.DoesNotExist:
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
            if field['options']:
                choices = [(v, k) for k, v in field['options'].items()]

                if field.allows_multiple_values:
                    fields[field['name']] = IntegerSplitterField(
                        field['name'],
                        choices=choices,
                        description=field['description'],
                        validators=[validators.optional()],
                    )
                else:
                    fields[field['name']] = SelectField(
                        field['name'],
                        choices=choices,
                        coerce=int,
                        description=field['description'],
                        validators=[validators.optional()],
                        widget=widgets.TextInput()
                    )
            else:
                if field['is_comment_field']:
                    continue

                if field['represents_boolean']:
                    field_validators = [validators.optional()]
                else:
                    field_validators = [
                        validators.optional(),
                        validators.NumberRange(min=field['min_value'],
                                               max=field['max_value'])
                    ]

                fields[field['name']] = IntegerField(
                    field['name'],
                    description=field['description'],
                    validators=field_validators)

        fields['groups'].append(groupspec)

    form_class = type('QuestionnaireForm', (BaseQuestionnaireForm,), fields)

    return form_class(data)


class FormForm(SecureForm):
    name = StringField(_('Name'), validators=[validators.InputRequired()])
    prefix = StringField(_('Prefix'), validators=[validators.InputRequired()])
    form_type = SelectField(_('Form type'), choices=models.Form.FORM_TYPES,
                            validators=[validators.InputRequired()])
    require_exclamation = BooleanField(_('Require exclamation'))
    calculate_moe = BooleanField(_('Calculate MOE'))
    quality_checks_enabled = BooleanField(_('QA enabled'))
    accredited_voters_tag = StringField(_('Accredited voters tag'))
    blank_votes_tag = StringField(_('Blank votes tag'))
    invalid_votes_tag = StringField(_('Invalid votes tag'))
    registered_votes_tag = StringField(_('Registered voters tag'))
