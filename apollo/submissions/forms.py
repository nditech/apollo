# -*- coding: utf-8 -*-
from flask_babelex import lazy_gettext as _
from flask_wtf import FlaskForm
from wtforms import fields, validators, widgets
from wtforms_alchemy.fields import QuerySelectField

from apollo import models, services
from apollo.frontend import permissions


class HiddenQuerySelectField(QuerySelectField):
    def _value(self):
        if self.raw_data:
            return self.raw_data[0]
        elif self.data is not None:
            return self.data
        else:
            return '__None'


def validate_location(form):
    '''Overrides the default validation for the form
    by running it first, then ensuring that the location
    and participant are not both empty for an incident
    form'''
    result = FlaskForm.validate(form)
    if not result:
        return result

    if not form.participant.data and not form.location.data:
        form.location.errors.append(
            _('Participant and location cannot both be empty'))
        form.participant.errors.append(
            _('Participant and location cannot both be empty'))
        return False

    return True


def make_submission_edit_form_class(event, form):
    form_fields = {}

    STATUS_CHOICES = (
        ('', _('Unmarked')),
        ('confirmed', _('Confirmed')),
        ('rejected', _('Rejected')),
        ('citizen', _('Citizen Report')),
    )

    form_fields['participant'] = HiddenQuerySelectField(
        _('Participant'),
        allow_blank=True,
        blank_text=_('Participant'),
        query_factory=lambda: services.participants.find(
            participant_set_id=event.participant_set_id),
        widget=widgets.HiddenInput(),
        validators=[validators.Optional()]
    )

    form_fields['location'] = HiddenQuerySelectField(
        _('Location'),
        allow_blank=True,
        blank_text=_('Location'),
        query_factory=lambda: services.locations.find(
            location_set_id=event.location_set_id),
        widget=widgets.HiddenInput()
    )

    for index, group in enumerate(form.data['groups']):
        for field in group['fields']:
            if field.get('is_comment'):
                form_fields[field['tag']] = fields.StringField(
                    field['tag'],
                    description=field['description'],
                    validators=[validators.Optional()],
                    widget=widgets.TextArea()
                )
            elif field.get('options'):
                choices = [(v, k) for k, v in field['options'].items()]

                if field.get('is_multi_choice'):
                    form_fields[field['tag']] = fields.SelectMultipleField(
                        field['tag'],
                        choices=choices,
                        coerce=int,
                        description=field['description'],
                        filters=[lambda data: data if data else None],
                        validators=[validators.Optional()],
                        option_widget=widgets.CheckboxInput(),
                        widget=widgets.ListWidget()
                    )
                else:
                    form_fields[field['tag']] = fields.IntegerField(
                        field['tag'],
                        description=field['description'],
                        validators=[
                            validators.Optional(),
                            validators.AnyOf([v for v, k in choices])],
                        widget=widgets.TextInput()
                    )
            else:
                if form.form_type == 'CHECKLIST' or not field.get('is_boolean'):
                    form_fields[field['tag']] = fields.IntegerField(
                        field['tag'], description=field['description'],
                        validators=[
                            validators.Optional(),
                            validators.NumberRange(min=field['min'], max=field['max'])]
                    )
                else:
                    form_fields[field['tag']] = fields.BooleanField(
                        field['tag'],
                        description=field['description'],
                        filters=[lambda data: 1 if data else None],
                        validators=[validators.Optional()]
                    )

    # TODO: verification status required
    # if form.form_type == 'CHECKLIST' and permissions.edit_submission_quarantine_status.can():
    #     form_fields['verification_status'] = fields.SelectField(
    #         choices=models.Submission.VERI
    #     )
    if form.form_type == 'CHECKLIST' and permissions.edit_submission_quarantine_status.can():
        form_fields['quarantine_status'] = fields.SelectField(
            choices=models.Submission.QUARANTINE_STATUSES,
            filters=[lambda data: data if data else ''],
            validators=[validators.Optional()]
        )

    if form.form_type == 'INCIDENT':
        form_fields['status'] = fields.SelectField(
            choices=STATUS_CHOICES,
            filters=[lambda data: data if data else None],
            validators=[validators.optional()]
        )
        form_fields['description'] = fields.StringField(
            widget=widgets.TextArea()
        )
        form_fields['validate'] = validate_location

    return type(
        'SubmissionEditForm',
        (FlaskForm,),
        form_fields
    )
