# -*- coding: utf-8 -*-
from __future__ import absolute_import
from apollo.frontend import route
from apollo.frontend.dashboard import get_coverage
from apollo.deployments.forms import generate_event_selection_form
from apollo.models import LocationType
from apollo.services import (
    events, forms, submissions, locations, location_types)
from apollo.frontend.filters import dashboard_filterset
from apollo.frontend.helpers import (
    get_event, set_event, get_concurrent_events_list_menu)
from apollo.frontend import permissions
from flask import (
    Blueprint, redirect, render_template, request, url_for, g)
from flask.ext.babel import lazy_gettext as _
from flask.ext.menu import register_menu
from flask.ext.security import login_required
from functools import partial


bp = Blueprint('dashboard', __name__, template_folder='templates',
               static_folder='static')


@route(bp, '/')
@register_menu(
    bp, 'main.dashboard',
    _('Dashboard'), order=0,
    icon='<i class="glyphicon glyphicon-user glyphicon-home"></i>')
@login_required
def index():
    args = request.args.copy()

    # get variables from query params, or use (hopefully) sensible defaults
    group = args.pop('group', None)
    location_type_id = args.pop('locationtype', None)

    page_title = _('Dashboard')
    template_name = 'frontend/dashboard.html'

    event = get_event()

    if not args.get('checklist_form'):
        form = forms.find(
            events=event, form_type='CHECKLIST').order_by('name').first()
    else:
        form = forms.get_or_404(pk=args.get('checklist_form'))

    if form:
        args.setdefault('checklist_form', unicode(form.id))

    queryset = submissions.find(
        form=form,
        submission_type='M'
    )
    filter_ = dashboard_filterset()(queryset, data=args)

    obs_queryset = submissions.find(
        form=form,
        submission_type='O'
    )
    obs_filter_ = dashboard_filterset()(obs_queryset, data=args)

    location = None
    if args.get('location'):
        location = locations.get_or_404(pk=args.get('location'))

    # activate sample filter
    filter_form = filter_.form
    queryset = filter_.qs
    obs_queryset = obs_filter_.qs
    next_location_type = False

    if not group:
        data = get_coverage(queryset)
        obs_data = get_coverage(obs_queryset)
    else:
        page_title = page_title + u' · {}'.format(group)
        if not location_type_id:
            location_type = location_types.find(
                is_administrative=True).order_by('ancestor_count').first()
        else:
            location_type = LocationType.objects.get_or_404(
                pk=location_type_id)

        # get the requisite location type - the way the aggregation
        # works, passing in a 'State' location type won't retrieve
        # data for the level below the 'State' type, it will retrieve
        # it for the 'State' type. in general, this isn't the behaviour
        # we want, so we need to find the lower level types and get the
        # one we want (the first of the children)
        le_temp = [lt for lt in location_type.children
                   if lt.is_administrative]

        try:
            next_location_type = le_temp[0]
        except IndexError:
            next_location_type = None

        data = get_coverage(queryset, group, location_type)
        obs_data = get_coverage(obs_queryset, group, location_type)

    # load the page context
    location_id = args.pop('location', '')
    context = {
        'args': args,
        'location_id': location_id,
        'next_location': bool(next_location_type),
        'data': data,
        'obs_data': obs_data,
        'filter_form': filter_form,
        'page_title': page_title,
        'location': location,
        'locationtype': getattr(next_location_type, 'id', ''),
        'group': group or ''
    }

    return render_template(
        template_name,
        **context
    )


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
            event = events.get_or_404(pk=form.event.data)

            set_event(event)
            return redirect(url_for('dashboard.index'))

    return render_template(template_name, form=form, page_title=page_title)
