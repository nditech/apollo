# -*- coding: utf-8 -*-
from datetime import datetime
from functools import partial
from itertools import ifilter
from mongoengine import signals
from wtforms import (
    Form,
    IntegerField, SelectField, SelectMultipleField, StringField,
    validators, widgets
)
from flask import g
from flask.ext.mongoengine.wtf import model_form
from flask.ext.wtf import Form as SecureForm
from .. import services, models
from ..frontend.helpers import DictDiffer
from ..participants.utils import update_participant_completion_rating
from .custom_fields import IntegerSplitterField
import json
import re


ugly_phone = re.compile('[^\d]*')


def update_submission_version(sender, document, **kwargs):
    if sender != services.submissions.__model__:
        return

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
    event = getattr(g, 'event', services.events.default())
    events = set(services.events.overlapping_events(event)).intersection(
        form.events)

    participant = models.Participant.objects(
            event__in=events, participant_id=participant_id).first()

    return participant


class BaseQuestionnaireForm(Form):
    form = StringField(
        u'Form', validators=[validators.required()],
        filters=[lambda data: services.forms.get(pk=data)])
    sender = StringField(u'Sender', validators=[validators.required()])
    comment = StringField(u'Comment', validators=[validators.optional()])

    def process(self, formdata=None, obj=None, **kwargs):
        self._formdata = formdata
        return super(BaseQuestionnaireForm, self).process(
            formdata, obj, **kwargs)

    def validate(self, *args, **kwargs):
        success = super(BaseQuestionnaireForm, self).validate(*args, **kwargs)
        if success and self._formdata:
            unknown_fields = filter(
                lambda f: f not in self._fields.keys(),
                self._formdata.keys())
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
        ignored_fields.extend(self.errors.keys())
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
                form_fields = filter(lambda f: f not in ignored_fields,
                                     self.data.keys())
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
                    phone_contact = next(ifilter(
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

                    with signals.post_save.connected_to(
                        update_submission_version,
                        sender=services.submissions.__model__
                    ):
                        submission.save()

                    # update completion rating for participant
                    if submission.form.form_type == 'CHECKLIST':
                        update_participant_completion_rating(participant)
        except models.Submission.DoesNotExist:
            pass

        return submission


def build_questionnaire(form, data=None):
    fields = {'groups': []}
    fields['participant'] = StringField(
        u'Participant',
        filters=[partial(filter_participants, form)],
        validators=[validators.required()])

    for group in form.groups:
        groupspec = (group.name, [])

        for field in group.fields:
            # if the field has options, create a list of choices
            if field.options:
                choices = [(v, k) for k, v in field.options.iteritems()]

                if field.allows_multiple_values:
                    fields[field.name] = IntegerSplitterField(
                        field.name,
                        choices=choices,
                        description=field.description,
                        validators=[validators.optional()],
                    )
                else:
                    fields[field.name] = SelectField(
                        field.name,
                        choices=choices,
                        coerce=int,
                        description=field.description,
                        validators=[validators.optional()],
                        widget=widgets.TextInput()
                    )
            else:
                if form.form_type == 'CHECKLIST':
                    fields[field.name] = IntegerField(
                        field.name,
                        description=field.description,
                        validators=[
                            validators.optional(),
                            validators.NumberRange(min=field.min_value,
                                                   max=field.max_value)]
                    )
                else:
                    fields[field.name] = IntegerField(
                        field.name,
                        description=field.description,
                        validators=[validators.optional()]
                    )

        fields['groups'].append(groupspec)

    form_class = type('QuestionnaireForm', (BaseQuestionnaireForm,), fields)


    return form_class(data)

FormForm = model_form(
    models.Form, SecureForm,
    only=[
        'name', 'prefix', 'form_type', 'require_exclamation', 'events',
        'calculate_moe', 'accredited_voters_tag', 'verifiable',
        'invalid_votes_tag', 'registered_voters_tag', 'blank_votes_tag',
        'permitted_roles'])
