from flask import g
from flask.ext.babel import lazy_gettext as _
from flask.ext.wtf import Form as WTSecureForm
from wtforms import SelectField, validators
from apollo.services import events


def generate_event_selection_form(*args, **kwargs):
    event_choices = events.find().order_by('-end_date').scalar('id', 'name')
    choices = [(unicode(a), unicode(b)) for a, b in event_choices]

    class EventSelectionForm(WTSecureForm):
        event = SelectField(
            _('Choose Event'),
            choices=choices,
            default=g.event.id,
            validators=[validators.input_required()]
        )

    return EventSelectionForm(*args, **kwargs)
