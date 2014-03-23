# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from flask import (
    Blueprint, abort, flash, g, redirect, render_template,
    request, session, url_for
)
from flask.ext.babel import lazy_gettext as _
from ..analyses.dashboard import get_coverage
from ..deployments.forms import generate_event_selection_form
from ..models import Event, Form, Location, LocationType, Sample, Submission
from . import route
from .forms import generate_dashboard_filter_form
from .helpers import get_form_context

bp = Blueprint('dashboard', __name__, template_folder='templates',
               static_folder='static', static_url_path='/core/static')


@route(bp, '/')
def index():
    # get variables from query params, or use (hopefully) sensible defaults
    group = request.args.get('group')
    location_type_id = request.args.get('locationtype')

    if request.args.get('form'):
        form = Form.objects.with_id(request.args.get('form'))
    else:
        form = Form.objects(deployment=g.get('deployment'),
                            form_type='CHECKLIST',
                            events=g.get('event')).first()

    if form is None:
        abort(404)

    page_title = _('Dashboard')
    template_name = 'core/nu_dashboard.html'

    filter_form = generate_dashboard_filter_form(g.get('deployment'),
                                                 g.get('event'))
    # only pick observer-created submissions
    queryset = Submission.objects(
        contributor__ne=None,
        created__lte=g.get('event').end_date,
        created__gte=g.get('event').start_date,
        deployment=g.get('deployment'),
        form=form,
    )

    # activate sample filter
    if request.args.get('sample'):
        sample = Sample.objects.get_or_404(request.args.get('sample'))
        locations = Location.objects(deployment=g.get('deployment'),
                                     samples=sample)
        queryset = queryset.filter(location__in=locations)

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
        try:
            sub_location_type = [
                lt for lt in location_type.get_children()
                if lt.on_dashboard_view][0]
        except IndexError:
            sub_location_type = location_type

        data = get_coverage(queryset, group, sub_location_type)

    # load the page context
    context = get_form_context(g.get('deployment'), g.get('event'))
    context.update(data=data, filter_form=filter_form, page_title=page_title)

    return render_template(
        template_name,
        **context
    )


@route(bp, '/event', methods=['GET', 'POST'])
def event_selection():
    page_title = _('Select event')
    template_name = 'frontend/event_selection.html'

    if request.method == 'GET':
        form = generate_event_selection_form()
    elif request.method == 'POST':
        form = generate_event_selection_form(request.form)

        if form.validate():
            try:
                event = Event.objects.get(pk=form.event.data)
            except Event.DoesNotExist:
                flash(_('Selected event not found'))
                return render_template(
                    template_name,
                    form=form,
                    page_title=page_title
                )

            session['event'] = unicode(event.id)
            return redirect(url_for('core.index'))

    return render_template(template_name, form=form, page_title=page_title)
