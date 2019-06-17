# -*- coding: utf-8 -*-
from flask_babelex import lazy_gettext as _
from flask_wtf import FlaskForm as WTSecureForm
from flask_wtf.file import FileField
from wtforms import (BooleanField, FloatField, IntegerField, SelectField,
                     SelectMultipleField, StringField, validators, widgets)
from wtforms.validators import Optional

from apollo.frontend import permissions

from ..locations.models import LocationType, Location
from ..participants.models import (
    Participant, ParticipantRole, ParticipantPartner)
from ..submissions.models import Submission
from .filters import LocationQuerySelectField, SupervisorQuerySelectField


def _make_choices(qs, placeholder=None):
    if placeholder:
        return [['', placeholder]] + [[str(i[0]), i[1]] for i in qs]
    else:
        return [['', '']] + [[str(i[0]), i[1]] for i in qs]


def generate_location_edit_form(location, data=None):
    initial_data = {
        'name': location.name,
        'lat': location.lat,
        'lon': location.lon
    }

    class LocationEditForm(WTSecureForm):
        name = StringField(_('Name'), validators=[validators.input_required()])
        lat = FloatField(_('Latitude'), [Optional()])
        lon = FloatField(_('Longitude'), [Optional()])

    return LocationEditForm(formdata=data, **initial_data)


def generate_participant_edit_form(participant, data=None):
    p_set_id = participant.participant_set_id
    role_choices = ParticipantRole.query.filter(
        ParticipantRole.participant_set_id == p_set_id).with_entities(
            ParticipantRole.id, ParticipantRole.name)
    partner_choices = ParticipantPartner.query.filter(
        ParticipantPartner.participant_set_id == p_set_id).with_entities(
            ParticipantPartner.id, ParticipantPartner.name)
    languages = participant.participant_set.deployment.languages

    attributes = {
        f'name_{locale}': StringField(_('Name (%(language)s)', language=lang))
        for locale, lang in languages.items()
    }
    attributes['gender'] = SelectField(_('Gender'), choices=Participant.GENDER)
    attributes['role'] = SelectField(
        _('Role'), choices=_make_choices(role_choices),
        validators=[validators.input_required()]
    )
    attributes['supervisor'] = SupervisorQuerySelectField(
        _('Supervisor'), validators=[validators.optional()], allow_blank=True,
        blank_text=_('Participant'),
        query_factory=lambda: Participant.query.filter(
            Participant.id == participant.supervisor.id if participant.supervisor else None),  # noqa
            get_pk=lambda i: i.id)
    attributes['location'] = LocationQuerySelectField(
        _('Location'), validators=[validators.input_required()],
        query_factory=lambda: Location.query.filter(
            Location.id == participant.location.id if participant.location else None),  # noqa
            get_pk=lambda i: i.id)
    attributes['partner'] = SelectField(
        _('Partner'), choices=_make_choices(partner_choices))
    attributes['phone'] = StringField(_('Phone'))
    attributes['password'] = StringField(_('Password'))

    participant_set = participant.participant_set

    if participant_set.extra_fields:
        attributes.update({
            f.name: StringField(f.label)
            for f in participant_set.extra_fields
        })

    ParticipantEditForm = type(
        'ParticipantEditForm', (WTSecureForm,), attributes)

    kwargs = {
        'formdata': data,
        'location': participant.location,
        'gender': participant.gender.code if participant.gender else '',
        'role': participant.role.id if participant.role else None,
        'partner': participant.partner.id if participant.partner else None,
        'supervisor': participant.supervisor,
        'phone': participant.primary_phone,
        'password': participant.password,
    }
    kwargs.update({
        f'name_{locale}': participant.name_translations.get(locale)
        for locale in languages.keys()
        if participant.name_translations.get(locale)
    })
    if participant_set.extra_fields and participant.extra_data:
        kwargs.update({
            f.name: participant.extra_data.get(f.name, '')
            for f in participant_set.extra_fields
        })

    return ParticipantEditForm(**kwargs)


def validate_location(form):
    val = WTSecureForm.validate(form)
    if not val:
        return val

    if not form.participant.data and not form.location.data:
        form.location.errors.append(
            _('Participant and Location cannot both be empty'))
        return False

    return True


def generate_submission_edit_form_class(form):
    form_fields = {}
    STATUS_CHOICES = (
        ('', _('Unmarked')),
        ('confirmed', _('Confirmed')),
        ('rejected', _('Rejected')),
        ('citizen', _('Citizen Report')),
    )

    # form_fields['contributor'] = CustomModelSelectField(
    #     _('Participant'),
    #     allow_blank=True,
    #     blank_text=_('Participant'),
    #     widget=widgets.HiddenInput(),
    #     validators=[validators.optional()],
    #     model=Participant,
    #     queryset=participants.find()
    #     )

    # form_fields['location'] = CustomModelSelectField(
    #     _('Location'),
    #     allow_blank=True,
    #     blank_text=_('Location'),
    #     widget=widgets.HiddenInput(),
    #     model=Location,
    #     queryset=locations.find()
    #     )

    for index, group in enumerate(form.groups):
        for field in group.fields:
            if field.is_comment_field:
                form_fields[field.name] = StringField(
                    field.name,
                    description=field.description,
                    widget=widgets.TextArea())
            elif field.options:
                choices = [(v, k) for k, v in field.options.items()]

                if field.allows_multiple_values:
                    form_fields[field.name] = SelectMultipleField(
                        field.name,
                        choices=choices,
                        coerce=int,
                        description=field.description,
                        filters=[lambda data: data if data else None],
                        validators=[validators.optional()],
                        option_widget=widgets.CheckboxInput(),
                        widget=widgets.ListWidget()
                    )
                else:
                    form_fields[field.name] = IntegerField(
                        field.name,
                        description=field.description,
                        validators=[
                            validators.optional(),
                            validators.AnyOf([v for v, k in choices])],
                        widget=widgets.TextInput()
                    )
            else:
                if form.form_type == 'CHECKLIST' or not field.represents_boolean:  # noqa
                    form_fields[field.name] = IntegerField(
                        field.name,
                        description=field.description,
                        validators=[
                            validators.optional(),
                            validators.NumberRange(min=field.min_value,
                                                   max=field.max_value)]
                    )
                else:
                    form_fields[field.name] = BooleanField(
                        field.name,
                        description=field.description,
                        filters=[lambda data: 1 if data else None],
                        validators=[validators.optional()]
                    )

    if (
        form.form_type == 'CHECKLIST' and
        permissions.edit_submission_quarantine_status.can()
    ):
        form_fields['quarantine_status'] = SelectField(
            choices=Submission.QUARANTINE_STATUSES,
            filters=[lambda data: data if data else ''],
            validators=[validators.optional()]
            )

    if (
        form.form_type == 'CHECKLIST' and
        permissions.edit_submission_verification_status.can()
    ):
        form_fields['verification_status'] = SelectField(
            choices=Submission.VERIFICATION_STATUSES,
            filters=[lambda data: data if data else ''],
            validators=[validators.optional()]
            )

    if form.form_type == 'INCIDENT':
        form_fields['status'] = SelectField(
            choices=STATUS_CHOICES,
            filters=[lambda data: data if data else None],
            validators=[validators.optional()]
        )
        form_fields['description'] = StringField(
            widget=widgets.TextArea()
        )
        form_fields['validate'] = validate_location

    return type(
        'SubmissionEditForm',
        (WTSecureForm,),
        form_fields
    )


def file_upload_form(*args, **kwargs):
    class FileUploadForm(WTSecureForm):
        spreadsheet = FileField(
            _('Data File'),
        )

    return FileUploadForm(*args, **kwargs)


class DummyForm(WTSecureForm):
    select_superset = StringField(widget=widgets.HiddenInput())


def make_checklist_init_form(event):
    location_set_id = getattr(event, 'location_set_id', None)
    participant_set_id = getattr(event, 'participant_set_id', None)

    form_choices = [
        (form.id, form.name)
        for form in event.forms
        if form.form_type == 'CHECKLIST'
    ]

    location_type_choices = [(i.id, i.name) for i in LocationType.query.filter(
        LocationType.location_set_id == location_set_id)]

    participant_role_choices = ParticipantRole.query.filter(
        ParticipantRole.participant_set_id == participant_set_id
    ).with_entities(ParticipantRole.id, ParticipantRole.name)

    class ChecklistInitForm(WTSecureForm):
        form = SelectField(
            _('Form'),
            choices=_make_choices(form_choices, _('Select Form')),
            validators=[validators.input_required()])

        role = SelectField(
            _('Role'),
            choices=_make_choices(participant_role_choices, _('Select Role')),
            validators=[validators.input_required()])
        location_type = SelectField(
            _('Location Type'),
            choices=_make_choices(location_type_choices,
                                  _('Select Location Type')),
            validators=[validators.input_required()])

    return ChecklistInitForm()
