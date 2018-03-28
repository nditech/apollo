# -*- coding: utf-8 -*-
from functools import partial

from flask import (
    Blueprint, abort, g, redirect, render_template, request, url_for)
from flask_babelex import lazy_gettext as _
from flask_menu import register_menu
from flask_security import login_required
from sqlalchemy import func

from apollo.deployments.forms import generate_event_selection_form
from apollo.frontend import permissions, route
from apollo.frontend.dashboard import get_coverage
from apollo.frontend.filters import dashboard_filterset
from apollo.frontend.helpers import (
    get_event, set_event, get_concurrent_events_list_menu,
    get_checklist_form_dashboard_menu)
from apollo.models import Event, LocationType, LocationTypePath
from apollo.services import (
    events, forms, submissions, locations, location_types)


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

    event = get_event()
    if not form_id:
        form = forms.find(
            form_set_id=event.form_set_id, form_type='CHECKLIST'
        ).order_by('name').first()
    else:
        form = forms.fget_or_404(
            form_set_id=event.form_set_id, form_type='CHECKLIST', id=form_id)

    if form is not None:
        page_title = _('Dashboard · %(name)s', name=form.name)
    else:
        page_title = _('Dashboard')

    query = submissions.find(
        event_id=event.id, form=form, submission_type='M')
    # dashboard_filter = dashboard_filterset()(query, data=args)

    # queryset = submissions.find(
    #     form=form,
    #     submission_type='M'
    # )
    # filter_ = dashboard_filterset()(queryset, data=args)

    # obs_queryset = submissions.find(
    #     form=form,
    #     submission_type='O'
    # )
    # obs_filter_ = dashboard_filterset()(obs_queryset, data=args)

    location = None
    if args.get('location'):
        location = locations.fget_or_404(
            id=args.get('location'), location_set_id=event.location_set_id)

    # # activate sample filter
    # filter_form = filter_.form
    # queryset = filter_.qs
    # obs_queryset = obs_filter_.qs
    # next_location_type = False

    if not group_slug:
        data = get_coverage(query, form)
        # obs_data = get_coverage(obs_queryset)
    else:
        group = next(
            (grp for grp in form.data['groups'] 
             if grp['slug'] == group_slug), None)
        if group is None:
            abort(404)
        page_title = _(
            'Dashboard · %(name)s  · %(group)s',
            name=form.name, group=group['name'])

        admin_location_types = location_types.find(
            is_administrative=True, location_set_id=event.location_set_id
        ).join(
            LocationType.ancestor_paths
        ).group_by(
            LocationType.id
        ).order_by(func.count(LocationType.ancestor_paths)).all()

        location_type = None
        if location_type_id:
            index, location_type = next(
                (pair for pair in enumerate(admin_location_types)
                 if pair[1].id == location_type_id),
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

        data = get_coverage(query, form, group, location_type)

    #     # get the requisite location type - the way the aggregation
    #     # works, passing in a 'State' location type won't retrieve
    #     # data for the level below the 'State' type, it will retrieve
    #     # it for the 'State' type. in general, this isn't the behaviour
    #     # we want, so we need to find the lower level types and get the
    #     # one we want (the first of the children)
    #     le_temp = [lt for lt in location_type.children
    #                if lt.is_administrative]

    #     try:
    #         next_location_type = le_temp[0]
    #     except IndexError:
    #         next_location_type = None

    #     data = get_coverage(queryset, group, location_type)
    #     obs_data = get_coverage(obs_queryset, group, location_type)

    # # load the page context
    # location_id = args.pop('location', '')
    # context = {
    #     'args': args,
    #     'location_id': '',
    #     'next_location': False,
    #     'data': [],
    #     'obs_data': [],
    #     'filter_form': None,
    #     'page_title': 'page_title',
    #     'location': location,
    #     'locationtype': getattr(next_location_type, 'id', ''),
    #     'group': group or '',
    #     'form_id': str(form.pk) if form else None
    # }
    context = {
        'args': {},
        'location_id': '',
        'next_location': False,
        'data': data,
        'obs_data': [],
        'filter_form': None,
        'page_title': page_title,
        'location': location,
        'locationtype': getattr(next_location_type, 'id', ''),
        'group': group or '',
        'form_id': form.id or None
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


@route(bp, '/event', methods=['GET', 'POST'])
@register_menu(
    bp, 'user.events', _('Events'),
    visible_when=partial(lambda: permissions.view_events.can()))
@permissions.view_events.require(403)
@login_required
def event_selection():
    page_title = _('Choose Event')
    template_name = 'frontend/event_selection.html'

    if request.method == 'GET':
        form = generate_event_selection_form()
    elif request.method == 'POST':
        form = generate_event_selection_form(request.form)

        if form.validate():
            event = events.get_or_404(Event.id == form.event.data)

            set_event(event)
            return redirect(url_for('dashboard.index'))

    return render_template(template_name, form=form, page_title=page_title)
