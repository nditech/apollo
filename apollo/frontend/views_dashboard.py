# -*- coding: utf-8 -*-
from functools import partial

from flask import (
    Blueprint, abort, g, redirect, render_template, request, url_for, session)
from flask_babelex import lazy_gettext as _
from flask_menu import register_menu
from flask_security import login_required
from sqlalchemy import false, func

from ..deployments.forms import generate_event_selection_form
from ..frontend import permissions, route
from ..frontend.dashboard import get_coverage
from ..frontend.helpers import (
    get_event, set_event, get_concurrent_events_list_menu,
    get_checklist_form_dashboard_menu)
from ..locations.models import LocationType, Location
from ..deployments.models import Event
from ..submissions.filters import make_dashboard_filter
from ..submissions.models import Submission
from ..formsframework.models import Form
from apollo import models
from apollo.services import events

bp = Blueprint('dashboard', __name__, template_folder='templates',
               static_folder='static')


def main_dashboard(form_id=None):
    args = request.args.copy()

    # get variables from query params, or use (hopefully) sensible defaults
    group_slug = args.pop('group', None)
    group = None
    location_type_id = args.pop('locationtype', None)
    next_location_type = None

    template_name = 'frontend/dashboard.html'
    breadcrumbs = [_('Dashboard')]

    event = get_event()
    if not form_id:
        form = Form.query.join(
            Form.events
        ).filter(
            Form.events.contains(event),
            Form.form_type == 'CHECKLIST'
        ).order_by('name').first()
    else:
        form = Form.query.join(
            Form.events
        ).filter(
            Form.events.contains(event),
            Form.form_type == 'CHECKLIST',
            Form.id == form_id).first_or_404()

    filter_class = make_dashboard_filter(event)
    if form is not None:
        breadcrumbs.append(form.name)

    query_args = [
        Submission.event_id == event.id,
        Submission.form_id == form.id
    ] if form else [false()]
    if form:
        if form.track_data_conflicts:
            query_args.append(Submission.submission_type == 'M')
        else:
            query_args.append(Submission.submission_type == 'O')

    query = Submission.query.filter(*query_args).join(
            Location,
            Submission.location_id == Location.id
        )

    if 'participant' in session:
        participant = models.Participant.query.get(session['participant'])

        if participant:
            if group_slug:
                _location_query = models.Location.query.with_entities(
                    models.Location.id
                ).join(
                    models.LocationPath,
                    models.Location.id == models.LocationPath.descendant_id
                ).filter(
                    models.LocationPath.ancestor_id.in_(
                        [loc.id for loc in participant.location.parents()]))
            else:
                _location_query = models.Location.query.with_entities(
                    models.Location.id
                ).join(
                    models.LocationPath,
                    models.Location.id == models.LocationPath.descendant_id
                ).filter(
                    models.LocationPath.ancestor_id == participant.location_id)

            query = query.filter(
                models.Submission.location_id.in_(_location_query))

    query_filterset = filter_class(query, request.args)

    location = None
    if args.get('location'):
        location = Location.query.filter(
            Location.id == args.get('location'),
            Location.location_set_id == event.location_set_id).first_or_404()

    if not group_slug:
        data = get_coverage(query_filterset.qs, form)
    else:
        group = next(
            (grp for grp in form.data['groups']
             if grp['slug'] == group_slug), None)
        if group is None:
            abort(404)
        breadcrumbs.append(group['name'])

        admin_location_types = LocationType.query.filter(
            LocationType.is_administrative == True,  # noqa
            LocationType.location_set_id == event.location_set_id
        ).join(
            LocationType.ancestor_paths
        ).group_by(
            LocationType.id, models.LocationTypePath.depth
        ).order_by(models.LocationTypePath.depth).all()

        location_type = None
        if location_type_id:
            # pair[1].id needs to be cast to a str because location_type_id
            # is a string
            index, location_type = next(
                (pair for pair in enumerate(admin_location_types)
                 if str(pair[1].id) == location_type_id),
                (None, None))

        if location_type is None and len(admin_location_types) > 0:
            location_type = admin_location_types[0]
            try:
                next_location_type = admin_location_types[1]
            except IndexError:
                next_location_type = None
        elif location_type is not None:
            try:
                next_location_type = admin_location_types[index + 1]
            except IndexError:
                next_location_type = None
        else:
            group = None

        data = get_coverage(
            query, form, group, location_type)

    context = {
        'args': {},
        'location_id': '',
        'next_location': next_location_type,
        'data': data,
        'obs_data': [],
        'filter_form': query_filterset.form,
        'breadcrumbs': breadcrumbs,
        'location': location,
        'locationtype': getattr(next_location_type, 'id', ''),
        'group': group or '',
        'form_id': form.id if form else None
    }

    return render_template(
        template_name,
        **context
    )


@route(bp, '/')
@register_menu(
    bp, 'main.dashboard',
    _('Dashboard'), order=0,
    icon='<i class="glyphicon glyphicon-user glyphicon-home"></i>')
@login_required
def index():
    return main_dashboard()


@route(bp, '/dashboard/checklists/<form_id>')
@register_menu(
    bp, 'main.dashboard.checklists', _('Checklists'),
    icon='<i class="glyphicon glyphicon-check"></i>', order=0,
    visible_when=lambda: len(
        get_checklist_form_dashboard_menu(form_type='CHECKLIST')) > 0,
    dynamic_list_constructor=partial(
        get_checklist_form_dashboard_menu, form_type='CHECKLIST'))
@login_required
def checklists(form_id=None):
    return main_dashboard(form_id)


@route(bp, '/event/<event_id>', methods=['GET'])
@register_menu(
    bp, 'user.concurrent_events', _('Concurrent Events'),
    visible_when=partial(
        lambda: events.overlapping_events(g.event).count() > 1),
    dynamic_list_constructor=partial(get_concurrent_events_list_menu))
@login_required
def concurrent_events(event_id):
    event = events.overlapping_events(g.event).get_or_404(pk=event_id)
    if event:
        set_event(event)
    return redirect(url_for('dashboard.index'))


@route(bp, '/events', methods=['GET', 'POST'])
@register_menu(
    bp, 'user.events', _('Events'),
    visible_when=partial(lambda: permissions.view_events.can()))
@login_required
@permissions.view_events.require(403)
def event_selection():
    breadcrumbs = [_('Choose Event')]
    template_name = 'frontend/event_selection.html'

    if request.method == 'GET':
        form = generate_event_selection_form()
    elif request.method == 'POST':
        form = generate_event_selection_form(request.form)

        if form.validate():
            event = events.get_or_404(Event.id == form.event.data)

            set_event(event)
            return redirect(url_for('dashboard.index'))

    return render_template(template_name, form=form, breadcrumbs=breadcrumbs)
