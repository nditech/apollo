from __future__ import absolute_import
from __future__ import unicode_literals
from flask.ext.babel import lazy_gettext as _
from flask.ext.wtf import Form as WTSecureForm
from flask.ext.wtf.file import FileField
from wtforms import (
    BooleanField, IntegerField, RadioField, SelectField, SelectMultipleField,
    StringField, TextField, ValidationError, validators, widgets
)
from ..models import (
    LocationType, Participant
)
from ..services import (
    events, locations, participants, participant_partners, participant_roles
)


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
    class ParticipantEditForm(WTSecureForm):
        # participant_id = TextField(
        #     _('Participant ID'),
        #     validators=[validators.input_required()]
        # )
        name = TextField(
            _('Name'),
            validators=[validators.input_required()]
        )
        gender = SelectField(
            _('Gender'),
            choices=Participant.GENDER,
            validators=[validators.input_required()]
        )
        role = SelectField(
            _('Role'),
            choices=_make_choices(
                participant_roles.find().scalar('id', 'name')
            ),
            validators=[validators.input_required()]
        )
        supervisor = SelectField(
            _('Supervisor'),
            choices=_make_choices(
                participants.find().scalar('id', 'name')
            ),
            validators=[validators.input_required()]
        )
        location = SelectField(
            _('Location'),
            choices=_make_choices(
                locations.find().scalar('id', 'name')
            ),
            validators=[validators.input_required()]
        )
        # partners are not required
        partner = SelectField(
            _('Partner'),
            choices=_make_choices(
                participant_partners.find().scalar('id', 'name')
            ),
        )

    return ParticipantEditForm(
        formdata=data,
        # participant_id=participant.participant_id,
        name=participant.name,
        location=participant.location.id,
        gender=participant.gender.upper(),
        role=participant.role.id,
        partner=participant.partner.id,
        supervisor=participant.supervisor.id
    )


def generate_participant_import_mapping_form(headers, *args, **kwargs):
    default_choices = [['', _('Select header')]] + [(v, v) for v in headers]

    class ParticipantImportMappingForm(WTSecureForm):
        _headers = headers
        participant_id = SelectField(
            _('Participant ID'),
            choices=default_choices,
            validators=[validators.input_required()]
        )
        name = SelectField(
            _('Name'),
            choices=default_choices,
            validators=[validators.input_required()]
        )
        role = SelectField(
            _('Role'),
            choices=default_choices,
            validators=[validators.input_required()]
        )
        partner_org = SelectField(
            _('Partner'),
            choices=default_choices,
            validators=[validators.input_required()]
        )
        location_id = SelectField(
            _('Location ID'),
            choices=default_choices,
            validators=[validators.input_required()]
        )
        supervisor_id = SelectField(
            _('Supervisor'),
            choices=default_choices,
            validators=[validators.input_required()]
        )
        gender = SelectField(
            _('Gender'),
            choices=default_choices,
            validators=[validators.input_required()]
        )
        email = SelectField(
            _('Email'),
            choices=default_choices,
            validators=[validators.input_required()]
        )
        phone = TextField(
            _('Phone prefix'),
            validators=[validators.input_required()]
        )

        def validate(self):
            rv = super(ParticipantImportMappingForm, self).validate()

            # check that no two fields were assigned the same value
            form_data = {f.data for f in self}
            if len(form_data) < len(self._fields):
                self.errors.update(
                    me=_('Duplicate field assignment detected')
                )
                return False
            return rv

        def validate_phone(self, field):
            subset = [h for h in self._headers if h.startswith(field.data)]
            if not subset:
                raise ValidationError(_('Invalid prefix'))

    return ParticipantImportMappingForm(*args, **kwargs)


def generate_submission_edit_form_class(form):
    form_fields = {}

    for index, group in enumerate(form.groups):
        for field in group.fields:
            options = field.options

            if options:
                choices = [(v, k) for k, v in options.iteritems()]

                if field.allows_multiple_values:
                    form_fields[field.name] = SelectMultipleField(
                        field.name,
                        choices=choices,
                        coerce=int,
                        option_widget=widgets.CheckboxInput(),
                        widget=widgets.ListWidget(prefix_label=False)
                    )
                else:
                    form_fields[field.name] = RadioField(
                        field.name,
                        choices=choices,
                        coerce=int,
                    )
            else:
                if form.form_type == 'CHECKLIST':
                    form_fields[field.name] = IntegerField(
                        field.name,
                        validators=[validators.number_range(
                            min=field.min_value or 0,
                            max=field.max_value or 9999
                        )]
                    )
                else:
                    form_fields[field.name] = BooleanField(field.name)

    return type(str('SubmissionEditForm'), (WTSecureForm,), form_fields)


class ParticipantUploadForm(WTSecureForm):
    event = SelectField(
        _('Event'),
        choices=_make_choices(
            events.find().scalar('id', 'name'),
            _('Select event')
        ),
        validators=[validators.input_required()]
    )
    spreadsheet = FileField(
        _('Data file'),
        # validators=[FileRequired()]
    )


class DummyForm(WTSecureForm):
    select_superset = StringField(widget=widgets.HiddenInput())
