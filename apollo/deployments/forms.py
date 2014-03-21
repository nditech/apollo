from flask.ext.wtf import Form as WTSecureForm
from wtforms import SelectField, validators
from ..services import events


def generate_event_selection_form(*args, **kwargs):
    event_choices = events.find().order_by('-end_date').scalar('id', 'name')
    choices = [(unicode(a), unicode(b)) for a, b in event_choices]

    class EventSelectionForm(WTSecureForm):
        event = SelectField(
            'Select event',
            choices=choices,
            validators=[validators.input_required()]
        )

    return EventSelectionForm(*args, **kwargs)
