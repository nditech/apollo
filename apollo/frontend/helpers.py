from .. import models
from .. import services
from flask import session, request, abort, g, url_for
from flask.ext.principal import Permission, ItemNeed, RoleNeed
from urlparse import urlparse


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
            for form in filter(
                lambda f: Permission(ItemNeed('view_forms', f, 'object'),
                                     RoleNeed('admin')).can(),
                services.forms.find(**kwargs))]


def displayable_location_types(**kwargs):
    temp = services.location_types.find(**kwargs)
    return sorted(temp, None, lambda x: len(x.ancestors_ref))


def analysis_breadcrumb_data(form, location, tag=None,
                             analysis_type='process'):
    '''A helper function to populate the breadcrumb data structure
    for both analysis and verification views.'''
    loc_type_names = [
        lt.name for lt in services.location_types.find(is_political=True)]
    location_branch = list(location.ancestors_ref) + [location]
    displayed_locations = [
        loc for loc in location_branch if loc.location_type in loc_type_names]

    return {
        'form': form,
        'locations': displayed_locations,
        'tag': tag,
        'analysis_type': analysis_type
    }


def analysis_navigation_data(form, location, tag=None,
                             analysis_type='process'):
    '''A helper function for generating data for navigation
    links for the analysis views.'''
    loc_type_names = [
        lt.name for lt in services.location_types.find(is_political=True)]
    lower_locations = [
        loc for loc in location.children()
        if loc.location_type in loc_type_names]
    lower_locations.sort(key=lambda loc: loc.name)

    return {
        'form': form,
        'locations': lower_locations,
        'tag': tag,
        'analysis_type': analysis_type
    }


class DictDiffer(object):
    """
    from https://github.com/hughdbrown/dictdiffer

    Calculate the difference between two dictionaries as:
    (1) items added
    (2) items removed
    (3) keys same in both but changed values
    (4) keys same in both and unchanged values
    """
    def __init__(self, current_dict, past_dict):
        self.current_dict, self.past_dict = current_dict, past_dict
        self.current_keys, self.past_keys = [
            set(d.keys()) for d in (current_dict, past_dict)
        ]
        self.intersect = self.current_keys.intersection(self.past_keys)

    def added(self):
        return self.current_keys - self.intersect

    def removed(self):
        return self.past_keys - self.intersect

    def changed(self):
        return set(o for o in self.intersect
                   if self.past_dict[o] != self.current_dict[o])

    def unchanged(self):
        return set(o for o in self.intersect
                   if self.past_dict[o] == self.current_dict[o])
