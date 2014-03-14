from __future__ import absolute_import
from __future__ import unicode_literals
from flask.ext.wtf import Form as WTForm
from wtforms import SelectField, validators
from apollo.core.models import Event, Form, Sample


def _make_choices(qs):
    return [['', '']] + list(qs)


def generate_event_selection_form(deployment, *args, **kwargs):
    event_choices = Event.objects(
        deployment=deployment
    ).order_by('-end_date').scalar('id', 'name')
    choices = [(unicode(a), unicode(b)) for a, b in event_choices]

    class EventSelectionForm(WTForm):
        event = SelectField(
            'Select event',
            choices=choices,
            validators=[validators.input_required()]
        )

    return EventSelectionForm(*args, **kwargs)


def generate_dashboard_filter_form(deployment, default_event, data=None):
    events = Event.objects(deployment=deployment)
    forms = Form.objects(events__in=events, form_type='CHECKLIST')
    # location_types = LocationType.objects(events__in=events)
    samples = Sample.objects(events__in=events)

    class DashboardFilterForm(WTForm):
        event = SelectField(
            choices=_make_choices(events.scalar('id', 'name'))
        )
        form = SelectField(
            choices=_make_choices(forms.scalar('id', 'name'))
        )
        sample = SelectField(
            choices=_make_choices(samples.scalar('id', 'name'))
        )

    if data:
        return DashboardFilterForm(data)
    else:
        return DashboardFilterForm(event=default_event)
