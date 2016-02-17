from __future__ import absolute_import

from flask import g
from flask.ext.babel import lazy_gettext as _
from flask.ext.mongoengine.wtf.fields import ModelSelectField
from flask.ext.wtf import Form as WTSecureForm
from flask.ext.wtf.file import FileField
from slugify import slugify
from wtforms import (BooleanField, IntegerField, SelectField,
                     SelectMultipleField, StringField, TextField,
                     ValidationError, validators, widgets)

from apollo.models import (
    Location, LocationType, Participant, Submission)
from apollo.services import (
    events, location_types, locations,
    participant_partners, participant_roles, participants, forms)
from apollo.frontend import permissions


class CustomModelSelectField(ModelSelectField):
    def _value(self):
        if self.raw_data:
            return self.raw_data[0]
        elif self.data is not None:
            return self.data
        else:
            return '__None'


def _make_choices(qs, placeholder=None):
    if placeholder:
        return [['', placeholder]] + [[unicode(i[0]), i[1]] for i in list(qs)]
    else:
        return [['', '']] + [[unicode(i[0]), i[1]] for i in list(qs)]


def generate_location_edit_form(location, data=None):
    locs = LocationType.objects(deployment=location.deployment)

    class LocationEditForm(WTSecureForm):
        name = TextField('Name', validators=[validators.input_required()])
        code = TextField('Code', validators=[validators.input_required()])
        location_type = SelectField(
            _('Location type'),
            choices=_make_choices(
                locs.scalar('name', 'name'),
                _('Location type')
            ),
            validators=[validators.input_required()]
        )

    return LocationEditForm(formdata=data, **location._data)


def generate_participant_edit_form(participant, data=None):

    class ParticipantEditBaseForm(WTSecureForm):
        # participant_id = TextField(
        #     _('Participant ID'),
        #     validators=[validators.input_required()]
        # )
        name = TextField(
            _('Name')
        )
        gender = SelectField(
            _('Gender'),
            choices=Participant.GENDER
        )
        role = SelectField(
            _('Role'),
            choices=_make_choices(
                participant_roles.find().scalar('id', 'name')
            ),
            validators=[validators.input_required()]
        )
        supervisor = TextField(
            _('Supervisor')
        )
        location = TextField(
            _('Location'),
            validators=[validators.input_required()]
        )
        # partners are not required
        partner = SelectField(
            _('Partner'),
            choices=_make_choices(
                participant_partners.find().scalar('id', 'name')
            ),
        )
        phone = StringField(_('Phone'))
        password = StringField(_('Password'))

    attributes = {
        field.name: TextField(field.label)
        for field in g.deployment.participant_extra_fields
    }

    ParticipantEditForm = type('ParticipantEditForm', (ParticipantEditBaseForm,), attributes)

    kwargs = {field: getattr(participant, field, '') for field in attributes.keys()}

    return ParticipantEditForm(
        formdata=data,
        # participant_id=participant.participant_id,
        name=participant.name,
        location=participant.location.id if participant.location else None,
        gender=participant.gender.upper(),
        role=participant.role.id if participant.role else None,
        partner=participant.partner.id if participant.partner else None,
        supervisor=participant.supervisor.id
        if participant.supervisor else None,
        phone=participant.phone,
        password=participant.password,
        **kwargs
    )


def generate_participant_import_mapping_form(
    deployment, headers, *args, **kwargs
):
    default_choices = [['', _('Select column')]] + [(v, v) for v in headers]

    attributes = {
        '_headers': headers,
        'participant_id': SelectField(
            _('Participant ID'),
            choices=default_choices,
            validators=[validators.input_required()]
        ),
        'name': SelectField(
            _('Name'),
            choices=default_choices
        ),
        'partner_org': SelectField(
            _('Partner'),
            choices=default_choices
        ),
        'role': SelectField(
            _('Role'),
            choices=default_choices,
        ),
        'location_id': SelectField(
            _('Location ID'),
            choices=default_choices,
        ),
        'supervisor_id': SelectField(
            _('Supervisor'),
            choices=default_choices,
        ),
        'gender': SelectField(
            _('Gender'),
            choices=default_choices
        ),
        'email': SelectField(
            _('Email'),
            choices=default_choices,
        ),
        'password': SelectField(
            _('Password'),
            choices=default_choices,
        ),
        'phone': TextField(
            _('Phone prefix')
        ),
        'group': TextField(
            _('Group prefix')
        )
    }

    for field in deployment.participant_extra_fields:
        attributes[field.name] = SelectField(
            _('%(label)s', label=field.label),
            choices=default_choices
        )

    def validate_phone(self, field):
        if field.data:
            subset = [h for h in self._headers if h.startswith(field.data)]
            if not subset:
                raise ValidationError(_('Invalid phone prefix'))

    def validate_group(self, field):
        if field.data:
            subset = {h for h in self._headers if h.startswith(field.data)}
            if not subset:
                raise ValidationError(_('Invalid group prefix'))

    attributes['validate_phone'] = validate_phone
    attributes['validate_group'] = validate_group

    ParticipantImportMappingForm = type(
        'ParticipantImportMappingForm',
        (WTSecureForm,),
        attributes
    )

    return ParticipantImportMappingForm(*args, **kwargs)


def generate_location_update_mapping_form(
    deployment, headers, *args, **kwargs
):
    default_choices = [['', _('Select column')]] + [(v, v) for v in headers]

    attributes = {
        '_headers': headers,
    }

    for location_type in location_types.find():
        name = location_type.name
        slug = slugify(name, separator='_').lower()
        attributes['{}_name'.format(slug)] = SelectField(
            _('%(label)s Name', label=name),
            choices=default_choices
        )
        attributes['{}_code'.format(slug)] = SelectField(
            _('%(label)s Code', label=name),
            choices=default_choices
        )
        if location_type.has_political_code:
            attributes['{}_pcode'.format(slug)] = SelectField(
                _('%(label)s Geopolitical Code', label=name),
                choices=default_choices
            )
        if location_type.has_other_code:
            attributes['{}_ocode'.format(slug)] = SelectField(
                _('%(label)s Other Code', label=name),
                choices=default_choices
            )
        if location_type.has_registered_voters:
            attributes['{}_rv'.format(slug)] = SelectField(
                _('%(label)s Registered Voters', label=name),
                choices=default_choices
            )

    LocationUpdateMappingForm = type(
        'LocationUpdateMappingForm',
        (WTSecureForm,),
        attributes
    )

    return LocationUpdateMappingForm(*args, **kwargs)


def validate_location(form):
    val = WTSecureForm.validate(form)
    if not val:
        return val

    if not form.contributor.data and not form.location.data:
        form.location.errors.append(
            _('Contributor and location cannot both be empty'))
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

    form_fields['contributor'] = CustomModelSelectField(
        _('Participant'),
        allow_blank=True,
        blank_text=_('Participant'),
        widget=widgets.HiddenInput(),
        validators=[validators.optional()],
        model=Participant,
        queryset=participants.find()
        )

    form_fields['location'] = CustomModelSelectField(
        _('Location'),
        allow_blank=True,
        blank_text=_('Location'),
        widget=widgets.HiddenInput(),
        model=Location,
        queryset=locations.find()
        )

    for index, group in enumerate(form.groups):
        for field in group.fields:
            if field.is_comment_field:
                form_fields[field.name] = TextField(
                    field.name,
                    description=field.description,
                    widget=widgets.TextArea())
            elif field.options:
                choices = [(v, k) for k, v in field.options.iteritems()]

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
                if form.form_type == 'CHECKLIST':
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
        event = SelectField(
            _('Event'),
            choices=_make_choices(
                events.find().scalar('id', 'name'),
                _('Select Event')
            ),
            validators=[validators.input_required()]
        )
        spreadsheet = FileField(
            _('Data File'),
        )

    return FileUploadForm(*args, **kwargs)


class DummyForm(WTSecureForm):
    select_superset = StringField(widget=widgets.HiddenInput())


def make_checklist_init_form():
    class ChecklistInitForm(WTSecureForm):
        form = SelectField(
            _('Form'),
            choices=_make_choices(
                forms.find(
                    events=g.event, form_type='CHECKLIST').scalar(
                        'id', 'name'),
                _('Select form')),
            validators=[validators.input_required()])
        role = SelectField(
            _('Role'),
            choices=_make_choices(
                participant_roles.find().scalar('id', 'name'),
                _('Select role')),
            validators=[validators.input_required()])
        location_type = SelectField(
            _('Location type'),
            choices=_make_choices(
                location_types.find().scalar('id', 'name'),
                _('Select location type')),
            validators=[validators.input_required()])

    return ChecklistInitForm()
