# -*- coding: utf-8 -*-
from urllib.parse import urlparse

from flask import session, request, g, url_for, abort
from flask_babelex import get_locale
from flask_login import current_user
from flask_principal import Permission, ItemNeed, RoleNeed
from sqlalchemy import func

from apollo import models, services


def get_deployment(hostname):
    """
    Retrieves the deployment based on the host represented in the
    HTTP_HOST header sent by the web browser.

    :param hostname: The hostname
    """
    deployment = models.Deployment.find_by_hostname(hostname)
    if not deployment:
        deployment = models.Deployment.find_by_hostname('localhost')

    if not deployment:
        raise abort(404)
    else:
        return deployment


def get_event():
    """
    Retrieves the chosen event from the session and if not, selects
    the default event and persists it in the session
    """
    _id = session.get('event', None)
    if not _id:
        event = services.events.default()
        _id = event.id
        session['event'] = _id
    else:
        event = services.events.query.filter_by(id=_id).first()

    return event


def set_event(event):
    """
    Given an event, persists the event in the session

    :param event: The event
    """
    session['event'] = event.id
    g.event = event


def set_request_presets():
    """
    Sets preset values for variables like deployment and event
    globally so they can be reused by other components for restricting
    filter results by deployment and/or event, for instance.
    """
    session.permanent = True
    hostname = urlparse(request.url).hostname

    g.deployment = get_deployment(hostname)
    g.event = get_event()
    g.locale = get_locale()
    current_user.event = g.event


def get_form_list_menu(**kwargs):
    """Retrieves a list of forms that the user has access to and returns it
    in a format that can be rendered on the menu

    :param form_type: The form type for the forms to be retrieved
    """
    event = g.event
    form_set_id = event.form_set_id
    return [{'url': url_for('submissions.submission_list',
             form_id=form.id),
             'text': form.name,
             'icon': '<i class="glyphicon glyphicon-check"></i>',
             'visible': True}
            for form in [f for f in
                         services.forms.find(
                             **kwargs, form_set_id=form_set_id
                         ).order_by('name')
                         if Permission(ItemNeed('access_resource', f.resource_id, f.resource_type),
                                       RoleNeed('admin')).can()]]


def get_checklist_form_dashboard_menu(**kwargs):
    """Retrieves a list of forms that have the verification flag set

    :param form_type: The form type for the forms to be retrieved
    """
    event = g.event
    form_set_id = event.form_set_id
    return [{'url': url_for('dashboard.checklists',
             form_id=form.id),
             'text': form.name,
             'icon': '<i class="glyphicon glyphicon-check"></i>',
             'visible': True}
            for form in [f for f in
                         services.forms.find(
                             **kwargs, form_set_id=form_set_id
                         ).order_by('name')
                         if Permission(ItemNeed('access_resource', f.resource_id, f.resource_type),
                                       RoleNeed('admin')).can()]]


def get_concurrent_events_list_menu():
    """Retrieves a list of events that are running concurrently and returns it
    in a format that can be rendered on the menu
    """
    events_list = services.events.overlapping_events(g.event).order_by(
        models.Event.start.desc())

    return [{'url': url_for('dashboard.concurrent_events',
             event_id=event.id), 'text': event.name, 'visible': True,
             'active': get_event() == event}
            for event in events_list]


def get_quality_assurance_form_list_menu(**kwargs):
    """Retrieves a list of forms that have the verification flag set

    :param form_type: The form type for the forms to be retrieved
    """
    event = g.event
    form_set_id = event.form_set_id
    return [{'url': url_for('submissions.quality_assurance_list',
             form_id=form.id),
             'text': form.name,
             'icon': '<i class="glyphicon glyphicon-ok"></i>',
             'visible': True}
            for form in [f for f in
                         services.forms.find(
                             **kwargs, form_set_id=form_set_id
                         ).order_by('name')
                         if Permission(ItemNeed('access_resource', f.resource_id, f.resource_type),
                                       RoleNeed('admin')).can()]]


def get_quality_assurance_form_dashboard_menu(**kwargs):
    """Retrieves a list of forms that have the verification flag set

    :param form_type: The form type for the forms to be retrieved
    """
    event = g.event
    form_set_id = event.form_set_id
    return [{'url': url_for('submissions.quality_assurance_dashboard',
             form_id=form.id),
             'text': form.name,
             'icon': '<i class="glyphicon glyphicon-tasks"></i>',
             'visible': True}
            for form in [f for f in
                         services.forms.find(
                             **kwargs,
                             form_set_id=form_set_id).order_by('name')
                         if Permission(ItemNeed('access_resource', f.resource_id, f.resource_type),
                                       RoleNeed('admin')).can()]]


def displayable_location_types(**kwargs):
    return services.location_types.find(**kwargs).join(
        models.LocationTypePath,
        models.LocationType.id == models.LocationTypePath.descendant_id
    ).order_by(
        func.count(models.LocationType.id)
    ).group_by('id').all()


def analysis_breadcrumb_data(form, location, tag=None,
                             analysis_type='process'):
    '''A helper function to populate the breadcrumb data structure
    for both analysis and quality assurance views.'''
    loc_type_names = [
        lt.name for lt in services.location_types.find(
            is_political=True, location_set_id=location.location_set_id)]
    location_branch = location.ancestors() + [location]
    displayed_locations = [
        loc for loc in location_branch
        if loc.location_type.name in loc_type_names]

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
    next_analyzable_level_id = models.LocationTypePath.query.join(
        models.LocationType,
        models.LocationType.id == models.LocationTypePath.descendant_id
    ).filter(
        models.LocationType.id != location.location_type_id,
        models.LocationTypePath.depth > 0,
        models.LocationType.is_political == True,   # noqa
    ).order_by(
        models.LocationTypePath.depth
    ).with_entities(
        models.LocationType.id
    ).limit(1).scalar()

    lower_locations = models.LocationPath.query.join(
        models.Location,
        models.LocationPath.descendant_id == models.Location.id
    ).join(
        models.LocationType
    ).filter(
        models.LocationType.id == next_analyzable_level_id,
        models.LocationPath.ancestor_id == location.id,
        models.LocationPath.depth > 0
    ).with_entities(
        models.Location
    ).all()

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
