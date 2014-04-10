from .. import models
from .. import services
from flask import session, request, abort, g, url_for
from urlparse import urlparse


def gen_page_list(pager, window_size=10):
    if window_size > pager.pages:
        window_size = pager.pages
    window_size -= 1
    start = max(pager.page - (window_size / 2), 1)
    end = min(pager.page + (window_size / 2), pager.pages)

    diff = end - start
    if diff < window_size:
        shift = window_size - diff
        if (start - shift) > 0:
            start -= shift
        else:
            end += shift
    return range(start, end + 1)


def get_deployment(hostname):
    """
    Retrieves the deployment based on the host represented in the
    HTTP_HOST header sent by the web browser.

    :param hostname: The hostname
    """
    return models.Deployment.objects(hostnames=hostname).first()


def get_event():
    """
    Retrieves the chosen event from the session and if not, selects
    the default event and persists it in the session
    """
    _id = session.get('event', None)
    if not _id:
        _id = services.events.default()
        session['event'] = _id

    return _id


def set_event(event):
    """
    Given an event, persists the event in the session

    :param event: The event
    """
    session['event'] = event
    g.event = event


def set_request_presets():
    """
    Sets preset values for variables like deployment and event
    globally so they can be reused by other components for restricting
    filter results by deployment and/or event, for instance.
    """
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


def displayable_location_types(**kwargs):
    temp = services.location_types.find(**kwargs)
    return sorted(temp, None, lambda x: len(x.ancestors_ref))
