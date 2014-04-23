# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from . import route
from ..analyses.dashboard import get_coverage
from ..deployments.forms import generate_event_selection_form
from ..models import LocationType
from ..services import events, forms, submissions
from .filters import DashboardFilterSet
from .helpers import get_event, set_event
from . import permissions
from flask import (
    Blueprint, redirect, render_template, request, url_for
)
from flask.ext.babel import lazy_gettext as _
from flask.ext.menu import register_menu
from flask.ext.security import login_required

bp = Blueprint('dashboard', __name__, template_folder='templates',
               static_folder='static')


@route(bp, '/')
@register_menu(bp, 'dashboard', _('Dashboard'))
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
        form = forms.find(events=event, form_type='CHECKLIST').first()
    else:
        form = forms.get(pk=args.get('checklist_form'))
    args.setdefault('checklist_form', unicode(form.id))

    queryset = submissions.find(
        contributor__ne=None,
        created__lte=event.end_date,
        created__gte=event.start_date
    )
    filter_ = DashboardFilterSet(queryset, data=args)

    # activate sample filter
    filter_form = filter_.form
    queryset = filter_.qs
    should_expand = True

    if not group:
        data = get_coverage(queryset)
    else:
        page_title = page_title + ' · {}'.format(group)
        if not location_type_id:
            location_type = LocationType.root()
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
                   if lt.on_dashboard_view]
        try:
            sub_location_type = le_temp[0]
        except IndexError:
            sub_location_type = location_type

        try:
            next_location_type = le_temp[1]
            location_type_id = next_location_type.id
        except IndexError:
            next_location_type = None
            should_expand = False
            location_type_id = None

        data = get_coverage(queryset, group, sub_location_type)

    # load the page context
    context = {
        'args': args,
        'data': data,
        'filter_form': filter_form,
        'page_title': page_title,
        'locationtype': location_type_id or '',
        'group': group or '',
        'should_expand': should_expand
    }

    return render_template(
        template_name,
        **context
    )


@route(bp, '/event', methods=['GET', 'POST'])
@register_menu(
    bp, 'events', _('Events'),
    visible_when=lambda: permissions.view_events.can())
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
