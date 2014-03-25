from .. import models
from .. import services
from flask import session, request, abort, g, url_for
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
    return models.Deployment.objects(hostnames=hostname).first()


def get_event():
    _id = session.get('event', None)
    if not _id:
        _id = services.events.default()
        session['event'] = _id

    return _id


def set_event(event):
    session['event'] = event
    g.event = event


def get_form_context(deployment, event=None):
    _forms = services.forms.get_all()

    if event:
        _forms = services.forms.find(events=event)

    checklist_forms = services.forms.find(
        form_type='CHECKLIST').order_by('name')
    incident_forms = services.forms.find(
        form_type='INCIDENT').order_by('name')

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
    except models.Deployment.DoesNotExist, models.Event.DoesNotExist:
        abort(404)


def get_form_list_menu(**kwargs):
    """Retrieves a list of forms that the user has access to and returns it
    in a format that can be rendered on the menu

    :param form_type: The form type for the forms to be retrieved
    TODO: Actually restrict forms based on user permissions
    """
    return [{'url': url_for('submissions.submission_list',
             form_id=str(form.id)), 'text': form.name, 'visible': True}
            for form in services.forms.find(**kwargs)]
