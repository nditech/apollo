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
from flask import (
    Blueprint, g, redirect, render_template, request, url_for
)
from flask.ext.babel import lazy_gettext as _
from flask.ext.menu import register_menu
from flask.ext.security import current_user
from flask.ext.security.decorators import roles_accepted

bp = Blueprint('dashboard', __name__, template_folder='templates',
               static_folder='static', static_url_path='/core/static')


@route(bp, '/')
@register_menu(bp, 'dashboard', _('Dashboard'))
def index():
    # get variables from query params, or use (hopefully) sensible defaults
    group = request.args.get('group')
    location_type_id = request.args.get('locationtype')

    page_title = _('Dashboard')
    template_name = 'frontend/nu_dashboard.html'

    event = get_event()
    data = request.args.copy()

    if 'event' not in data:
        data.add('event', unicode(event.id))
    if 'form' not in data:
        form = forms.find(events=event, form_type='CHECKLIST').first()
        data.add('checklist_form', unicode(form.id))

    queryset = submissions.find(contributor__ne=None)
    filter_ = DashboardFilterSet(queryset, data=data)

    # activate sample filter
    filter_form = filter_.form
    queryset = filter_.qs
    should_expand = True

    if not group:
        data = get_coverage(queryset)
    else:
        page_title = page_title + ' · {}'.format(group)
        if location_type_id is None:
            location_type = LocationType.get_root_for_event(g.get('event'))
        else:
            location_type = LocationType.objects.get_or_404(
                pk=location_type_id)

        # get the requisite location type
        le_temp = [lt for lt in location_type.get_children()
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
@register_menu(bp, 'events', _('Events'), visible_when=lambda: any(
    [current_user.has_role(role) for role in ['admin', 'manager', 'analyst']]))
@roles_accepted('admin', 'analyst', 'manager')
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
