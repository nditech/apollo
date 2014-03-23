from ..models import Deployment, Event
from ..services import forms, events
from flask import session, request, abort, g
from urlparse import urlparse


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


def get_deployment(hostname):
    return str(Deployment.objects(hostnames=hostname).first().id)


def get_event():
    _id = session.get('event', None)
    if not _id:
        _id = str(events.default().id)
        session['event'] = _id

    return _id


def get_form_context(deployment, event=None):
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


def set_request_presets():
    hostname = urlparse(request.url).hostname

    try:
        g.deployment = get_deployment(hostname)
        g.event = get_event()
    except Deployment.DoesNotExist, Event.DoesNotExist:
        abort(404)
