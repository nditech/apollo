# -*- coding: utf-8 -*-
from flask_babel import gettext as _
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import fields, validators, widgets
from wtforms_alchemy.fields import QuerySelectField

from apollo import models
from apollo.frontend import permissions
from apollo.submissions.filters import (
    ParticipantQuerySelectField, LocationQuerySelectField)


class HiddenQuerySelectField(QuerySelectField):
    def _value(self):
        if self.raw_data:
            return self.raw_data[0]
        elif self.data is not None:
            return self.data
        else:
            return '__None'


class NumberStringRange(validators.NumberRange):
    def __call__(self, form, field):
        try:
            data = float(field.data)
        except ValueError:
            raise validators.ValidationError(
                field.gettext("Not a valid integer value"))

        if (
            data is None
            or (self.min is not None and data < self.min)
            or (self.max is not None and data > self.max)
        ):
            message = self.message
            if message is None:
                # we use %(min)s interpolation to support floats, None, and
                # Decimals without throwing a formatting exception.
                if self.max is None:
                    message = field.gettext("Number must be at least %(min)s.")
                elif self.min is None:
                    message = field.gettext("Number must be at most %(max)s.")
                else:
                    message = field.gettext(
                        "Number must be between %(min)s and %(max)s."
                    )

            raise validators.ValidationError(
                message % dict(min=self.min, max=self.max))


def single_choice_coerce(value):
    if value == '':
        return None

    return int(value)


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

    form_fields['participant'] = ParticipantQuerySelectField(
        _('Participant'),
        allow_blank=True,
        blank_text=_('Participant'),
        query_factory=lambda: [], get_pk=lambda i: i.id
    )

    form_fields['location'] = LocationQuerySelectField(
        _('Location'),
        allow_blank=True,
        blank_text=_('Location'),
        query_factory=lambda: [], get_pk=lambda i: i.id,
        validators=[validators.Optional()]
    )

    if form.data and 'groups' in form.data:
        for index, group in enumerate(form.data['groups']):
            for field in group['fields']:
                field_type = field.get('type')
                if field_type == 'comment':
                    form_fields[field['tag']] = fields.StringField(
                        field['tag'],
                        description=field['description'],
                        validators=[validators.Optional()],
                        widget=widgets.TextArea()
                    )
                elif field_type == 'string':
                    form_fields[field['tag']] = fields.StringField(
                        field['tag'],
                        description=field['description'],
                        validators=[validators.Optional(),
                                    NumberStringRange(
                                    min=field.get('min', 0),
                                    max=field.get('max', 9999))]
                    )
                elif field_type in ('select', 'multiselect'):
                    choices = [(v, '{} — {}'.format(v, k)) for k, v in sorted(
                        field['options'].items(), key=lambda x: x[1])]

                    if field_type == 'multiselect':
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
                        render_choices = [('', '')] + choices
                        form_fields[field['tag']] = fields.SelectField(
                            field['tag'],
                            choices=render_choices,
                            coerce=single_choice_coerce,
                            description=field['description'],
                            filters=[lambda data: data if data else None],
                            validators=[validators.Optional()]
                        )
                elif field_type == 'image':
                    form_fields[field['tag']] = FileField(
                        field['tag'],
                        description=field['description'],
                        validators=[
                            FileAllowed(
                                ['jpg', 'png'],
                                _('Please select a JPG or PNG image to upload'),
                            )
                        ]
                    )
                else:
                    if field_type in ('category', 'integer'):
                        form_fields[field['tag']] = fields.IntegerField(
                            field['tag'], description=field['description'],
                            validators=[
                                validators.Optional(),
                                validators.NumberRange(
                                    min=field.get('min', 0),
                                    max=field.get('max', 9999))]
                        )
                    elif field_type == 'boolean':
                        form_fields[field['tag']] = fields.BooleanField(
                            field['tag'],
                            description=field['description'],
                            filters=[lambda data: 1 if data else None],
                            validators=[validators.Optional()]
                        )

    if form.form_type in ['CHECKLIST', 'SURVEY']:
        if permissions.edit_submission_quarantine_status.can():
            form_fields['quarantine_status'] = fields.SelectField(
                choices=models.Submission.QUARANTINE_STATUSES,
                filters=[lambda data: data if data else ''],
                validators=[validators.Optional()]
            )
        if permissions.edit_submission_verification_status.can():
            form_fields['verified_fields'] = fields.SelectMultipleField(
                _('Verified'),
                choices=[(tag, tag) for tag in form.tags],
                option_widget=widgets.CheckboxInput(),
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

    form_fields['unreachable'] = fields.BooleanField()

    return type(
        'SubmissionEditForm',
        (FlaskForm,),
        form_fields
    )


def generate_image_delete_form_class(submission):
    class ImageAttachmentDeleteForm(FlaskForm):
        tag = fields.SelectField(choices=submission.form.get_image_fields())

    return ImageAttachmentDeleteForm
