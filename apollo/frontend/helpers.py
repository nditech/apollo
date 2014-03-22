from ..models import Event
from ..services import forms
from flask import session
from mongoengine import ValidationError


def gen_page_list(page, num_pages, window_size=9):
    start = max(page - (window_size / 2), 1)
    end = min(page - (window_size / 2), num_pages)
    diff = end - start
    if diff < window_size:
        shift = window_size - diff
        if start - shift > 0:
            start -= shift
        else:
            end += shift
    return range(start, end + 1)


def _get_event(container):
    try:
        _id = container.get('event')
        if not _id:
            return Event.default()

        event = Event.objects.with_id(_id)
    except (KeyError, TypeError, ValueError, ValidationError) as e:
        event = Event.default()

    return event


def select_default_event(app, user):
    event = _get_event(session)
    session['event'] = unicode(event.id)


def _get_form_context(deployment, event=None):
    _forms = forms.get_all()

    if event:
        _forms = forms.find(events=event)

    checklist_forms = forms.find(form_type='CHECKLIST').order_by('name')
    incident_forms = forms.find(form_type='INCIDENT').order_by('name')

    return {
        'forms': _forms,
        'checklist_forms': checklist_forms,
        'incident_forms': incident_forms
    }
