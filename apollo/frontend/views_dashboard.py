# -*- coding: utf-8 -*-
from functools import partial

from flask import (
    Blueprint, abort, g, redirect, render_template, request, url_for, session)
from flask_babelex import lazy_gettext as _
from flask_menu import register_menu
from flask_security import login_required
from sqlalchemy import false

from ..deployments.forms import generate_event_selection_form
from ..frontend import permissions, route
from ..frontend.dashboard import (
    event_days, get_coverage, get_daily_progress,
    get_stratified_daily_progress)
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
    stratified_progress = args.pop('progress', None)
    group = None
    location_type_id = args.pop('locationtype', None)
    next_location_type = None
    chart_type = args.pop('chart', None)
    data_view = args.pop('view', None)
    if chart_type:
        session['dashboard_chart_type'] = chart_type if chart_type in [
            'pie', 'bar'] else 'pie'
    if data_view:
        session['dashboard_data_view'] = data_view if data_view in [
            'divisions', 'locations'] else 'divisions'
    daily_progress = {}
    daily_stratified_progress = []

    template_name = 'frontend/dashboard.html'
    breadcrumbs = [_('Response Rate Dashboard')]

    event = get_event()
    if not form_id:
        form = Form.query.join(
            Form.events
        ).filter(
            Form.events.contains(event),
            Form.form_type.in_(['CHECKLIST', 'SURVEY']),
            Form.is_hidden == False, # noqa
        ).order_by('name').first()
    else:
        form = Form.query.join(
            Form.events
        ).filter(
            Form.is_hidden == False, # noqa
            Form.events.contains(event),
            Form.form_type.in_(['CHECKLIST', 'SURVEY']),
            Form.id == form_id).first_or_404()

    filter_on_locations = not form.untrack_data_conflicts if form else False
    filter_class = make_dashboard_filter(event, filter_on_locations)
    if form is not None:
        if group_slug:
            breadcrumbs.append({'text': form.name, 'url': url_for('dashboard.response_rate', form_id=form.id)})  # noqa
        else:
            breadcrumbs.append({'text': form.name})

    query_args = [
        Submission.event_id == event.id,
        Submission.form_id == form.id
    ] if form else [false()]
    if form:
        if not form.untrack_data_conflicts and form.form_type == 'CHECKLIST':
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

    location = None
    if args.get('location_'):
        location = Location.query.filter(
            Location.id == args.get('location_'),
            Location.location_set_id == event.location_set_id).first_or_404()

    if (
        group_slug and
        location and
        session.get('dashboard_data_view') == 'locations'
    ):
        _location_query = models.Location.query.with_entities(
            models.Location.id
        ).join(
            models.LocationPath,
            models.Location.id == models.LocationPath.descendant_id
        ).filter(models.LocationPath.ancestor_id == location.id)

        query = query.filter(
            models.Submission.location_id.in_(_location_query))

    query_filterset = filter_class(query, request.args)

    if not group_slug:
        data = get_coverage(query_filterset.qs, form)
        if form and form.show_progress and not stratified_progress:
            daily_progress = get_daily_progress(query_filterset.qs, event)
        elif form and form.show_progress and stratified_progress:
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
                stratified_progress = None

            daily_stratified_progress = get_stratified_daily_progress(
                query, event, location_type)
    else:
        group = next(
            (grp for grp in form.data['groups']
             if grp['slug'] == group_slug), None)
        if group is None:
            abort(404)

        if location:
            breadcrumbs.append({
                'text': group['name'],
                'url': url_for(
                    'dashboard.response_rate',
                    form_id=form.id,
                    group=group_slug)})
        else:
            breadcrumbs.append({'text': group['name']})

        admin_location_types = LocationType.query.filter(
            LocationType.is_administrative == True,  # noqa
            LocationType.location_set_id == event.location_set_id
        ).join(
            LocationType.ancestor_paths
        ).group_by(
            LocationType.id, models.LocationTypePath.depth
        ).order_by(models.LocationTypePath.depth).all()

        if location:
            for ancestor in location.ancestors():
                if ancestor.location_type in admin_location_types:
                    idx, lt = next(
                        (pair for pair in enumerate(admin_location_types)
                         if pair[1].id == ancestor.location_type.id),
                        (None, None))
                    try:
                        breadcrumbs.append({
                            'text': ancestor.name,
                            'url': url_for(
                                'dashboard.response_rate', form_id=form.id,
                                group=group_slug,
                                locationtype=admin_location_types[idx + 1].id,
                                location_=ancestor.id)
                        })
                    except IndexError:
                        pass
            breadcrumbs.append({
                'text': location.name,
            })

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
            query_filterset.qs, form, group, location_type)

    context = {
        'args': {'sample': args.get('sample')},
        'location_id': '',
        'next_location': next_location_type,
        'data': data,
        'event_days': event_days(event),
        'daily_progress': daily_progress,
        'daily_stratified_progress': daily_stratified_progress,
        'obs_data': [],
        'filter_form': query_filterset.form,
        'breadcrumbs': breadcrumbs,
        'location': location,
        'locationtype': getattr(next_location_type, 'id', ''),
        'group': group or '',
        'form_id': form.id if form else None,
        'form': form
    }

    return render_template(
        template_name,
        **context
    )


@route(bp, '/')
@register_menu(
    bp, 'main.dashboard',
    _('Dashboard'), order=0)
@login_required
def index():
    return main_dashboard()


@route(bp, '/dashboard/<form_id>')
@register_menu(
    bp, 'main.dashboard.response_rate', _('Response Rate'),
    order=0,
    visible_when=lambda: len(
        get_checklist_form_dashboard_menu(form_type='CHECKLIST') +
        get_checklist_form_dashboard_menu(form_type='SURVEY')) > 0,
    dynamic_list_constructor=lambda:
        get_checklist_form_dashboard_menu(form_type='CHECKLIST') +
        get_checklist_form_dashboard_menu(form_type='SURVEY'))
@login_required
def response_rate(form_id=None):
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
