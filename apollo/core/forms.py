from __future__ import absolute_import
from __future__ import unicode_literals
from flask.ext.babel import lazy_gettext as _
from flask.ext.wtf import Form as WTSecureForm
from wtforms import (
    Form as WTForm, HiddenField, SelectField, TextField, validators
)
from apollo.core.models import (
    Event, Form, Location, LocationType, Participant,
    ParticipantPartner, ParticipantRole, Sample
)


def _make_choices(qs, placeholder=None):
    if placeholder:
        return [['', placeholder]] + [[unicode(i[0]), i[1]] for i in list(qs)]
    else:
        return [['', '']] + [[unicode(i[0]), i[1]] for i in list(qs)]


def generate_event_selection_form(deployment, *args, **kwargs):
    event_choices = Event.objects(
        deployment=deployment
    ).order_by('-end_date').scalar('id', 'name')
    choices = [(unicode(a), unicode(b)) for a, b in event_choices]

    class EventSelectionForm(WTSecureForm):
        event = SelectField(
            'Select event',
            choices=choices,
            validators=[validators.input_required()]
        )

    return EventSelectionForm(*args, **kwargs)


def generate_location_edit_form(location, data=None):
    locations = LocationType.objects(deployment=location.deployment)

    class LocationEditForm(WTSecureForm):
        name = TextField('Name', validators=[validators.input_required()])
        code = TextField('Code', validators=[validators.input_required()])
        location_type = SelectField(
            'Location type',
            choices=_make_choices(
                locations.scalar('name', 'name'),
                'Location type'
            ),
            validators=[validators.input_required()]
        )

    return LocationEditForm(formdata=data, **location._data)


def generate_participant_edit_form(participant, data=None):
    deployment = participant.deployment

    class ParticipantEditForm(WTSecureForm):
        participant_id = TextField(
            'Participant ID',
            validators=[validators.input_required()]
        )
        name = TextField(
            'Name',
            validators=[validators.input_required()]
        )
        gender = SelectField(
            'Gender',
            choices=Participant.GENDER,
            validators=[validators.input_required()]
        )
        role = SelectField(
            'Role',
            choices=_make_choices(
                ParticipantRole.objects.scalar('id', 'name')
            ),
            validators=[validators.input_required()]
        )
        supervisor = SelectField(
            'Supervisor',
            choices=_make_choices(
                Participant.objects(deployment=deployment).scalar('id', 'name')
            ),
            validators=[validators.input_required()]
        )
        location = SelectField(
            'Location',
            choices=_make_choices(
                Location.objects(deployment=deployment).scalar('id', 'name')
            ),
            validators=[validators.input_required()]
        )
        # partners are not required
        partner = SelectField(
            'Partner',
            choices=_make_choices(
                ParticipantPartner.objects.scalar('id', 'name')
            ),
        )

    return ParticipantEditForm(
        formdata=data,
        participant_id=participant.participant_id,
        name=participant.name,
        location=participant.location.id,
        gender=participant.gender.upper(),
        role=participant.role.id,
        partner=participant.partner.id,
        supervisor=participant.supervisor.id
    )


####################
# FILTER FORMS
####################

def generate_dashboard_filter_form(deployment, default_event, data=None):
    events = Event.objects(deployment=deployment)
    forms = Form.objects(
        deployment=deployment,
        events__in=events,
        form_type='CHECKLIST'
    )
    # location_types = LocationType.objects(events__in=events)
    samples = Sample.objects(deployment=deployment, events__in=events)

    class DashboardFilterForm(WTForm):
        event = SelectField(
            choices=_make_choices(events.scalar('id', 'name'), 'Event')
        )
        form = SelectField(
            choices=_make_choices(forms.scalar('id', 'name'), 'Form')
        )
        sample = SelectField(
            choices=_make_choices(samples.scalar('id', 'name'), 'Sample')
        )

    if data:
        return DashboardFilterForm(data)
    else:
        return DashboardFilterForm(event=default_event)


def generate_participant_filter_form(deployment, data=None, **kwargs):
    default_role = getattr(kwargs.pop('role', ''), 'id', '')
    default_partner = getattr(kwargs.pop('partner', ''), 'id', '')
    default_location = getattr(kwargs.pop('location', ''), 'id', '')
    default_sample = getattr(kwargs.pop('sample', ''), 'id', '')

    class ObserverFilterForm(WTForm):
        sample = SelectField(
            choices=_make_choices(
                Sample.objects(deployment=deployment).scalar('id', 'name'),
                _('Sample')
            ),
            default=default_sample
        )
        participant_id = TextField(default=kwargs.pop('participant_id', None))
        name = TextField(default=kwargs.pop('name', None))
        role = SelectField(
            choices=_make_choices(
                ParticipantRole.objects(
                    deployment=deployment
                )
                .scalar('id', 'name'),
                _('All roles')
            ),
            default=default_role
        )
        location = SelectField(
            choices=_make_choices(
                Location.objects(deployment=deployment).scalar('id', 'name'),
                _('Location')
            ),
            default=default_location
        )
        partner = SelectField(
            choices=_make_choices(
                ParticipantPartner.objects(
                    deployment=deployment
                )
                .scalar('id', 'name'),
                _('Partner')
            ),
            default=default_partner
        )

    return ObserverFilterForm(data, **kwargs)


def generate_submission_filter_form(form, default_event, data=None):
    samples = Sample.objects(deployment=form.deployment).scalar('id', 'name')
    locations = Location.objects(deployment=form.deployment).scalar('id', 'name')

    class SubmissionFilterForm(WTForm):
        participant_id = TextField()
        location = SelectField(choices=_make_choices(locations, _('Location')))
        event = HiddenField(default=unicode(default_event.id))
        sample = SelectField(choices=_make_choices(samples, _('Sample')))

    for group in form.groups:
        choices = [
            ('0', _('%(group)s Status', group=group.name)),
            ('1', _('%(group)s Partial', group=group.name)),
            ('2', _('%(group)s Missing', group=group.name)),
            ('3', _('%(group)s Complete', group=group.name))
        ]
        setattr(SubmissionFilterForm, 'group_{}'.format(group.slug), SelectField(choices=choices))

    if form.form_type == 'INCIDENT':
        setattr(
            SubmissionFilterForm,
            'status',
            SelectField(choices=(
                ('', _('Status')),
                ('NULL', _('Unmarked')),
                ('confirmed', _('Confirmed')),
                ('rejected', _('Rejected')),
                ('citizen', _('Citizen report')))
            )
        )

    return SubmissionFilterForm(data)
