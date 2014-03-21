# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from logging import getLogger
from flask import (
    Blueprint, abort, flash, g, redirect, render_template,
    request, session, url_for
)
from flask.ext.babel import lazy_gettext as _
from flask.ext.security import login_required
from ..analyses.dashboard import get_coverage
from .forms import (
    generate_dashboard_filter_form,
    generate_event_selection_form, generate_location_edit_form,
    generate_participant_edit_form, generate_submission_filter_form
)
from .models import (
    Event, Form, Location, LocationType, Participant, ParticipantPartner,
    ParticipantRole, Sample, Submission
)
from . import route

PAGE_SIZE = 25
core = Blueprint('core', __name__, template_folder='templates',
                 static_folder='static', static_url_path='/core/static')
logger = getLogger(__name__)


def _get_event(container):
    from mongoengine import ValidationError

    try:
        _id = container.get('event')
        if not _id:
            return Event.default()

        event = Event.objects.with_id(_id)
    except (KeyError, TypeError, ValueError, ValidationError) as e:
        logger.exception(e)
        event = Event.default()

    return event


def _get_form_context(deployment, event=None):
    forms = Form.objects(deployment=deployment)

    if event:
        forms = forms(events=event)

    checklist_forms = forms(form_type='CHECKLIST').order_by('name')
    incident_forms = forms(form_type='INCIDENT').order_by('name')

    return {
        'forms': forms,
        'checklist_forms': checklist_forms,
        'incident_forms': incident_forms
    }


@route(core, '/')
def index():
    # get variables from query params, or use (hopefully) sensible defaults
    deployment = g.get('deployment')
    if request.args.get('event'):
        event = Event.objects.with_id(request.args.get('event'))
        if event is None:
            abort(404)
    else:
        event = _get_event(session)

    group = request.args.get('group')
    location_type_id = request.args.get('locationtype')

    if request.args.get('form'):
        form = Form.objects.with_id(request.args.get('form'))
    else:
        form = Form.objects(deployment=deployment, form_type='CHECKLIST',
                            events=event).first()

    if form is None:
        abort(404)

    page_title = _('Dashboard')
    template_name = 'core/nu_dashboard.html'

    filter_form = generate_dashboard_filter_form(deployment, event)
    # only pick observer-created submissions
    queryset = Submission.objects(
        contributor__ne=None,
        created__lte=event.end_date,
        created__gte=event.start_date,
        deployment=deployment,
        form=form,
    )

    # activate sample filter
    if request.args.get('sample'):
        sample = Sample.objects.get_or_404(request.args.get('sample'))
        locations = Location.objects(deployment=deployment, samples=sample)
        queryset = queryset.filter(location__in=locations)

    if not group:
        data = get_coverage(queryset)
    else:
        page_title = page_title + ' · {}'.format(group)
        if location_type_id is None:
            location_type = LocationType.get_root_for_event(event)
        else:
            location_type = LocationType.objects.get_or_404(
                pk=location_type_id)

        # get the requisite location type
        try:
            sub_location_type = [
                lt for lt in location_type.get_children() if lt.on_dashboard_view][0]
        except IndexError:
            sub_location_type = location_type

        data = get_coverage(queryset, group, sub_location_type)

    # load the page context
    context = _get_form_context(deployment, event)
    context.update(data=data, filter_form=filter_form, page_title=page_title)

    return render_template(
        template_name,
        **context
    )


@route(core, '/event', methods=['GET', 'POST'])
def event_selection():
    page_title = _('Select event')
    template_name = 'frontend/event_selection.html'

    if request.method == 'GET':
        form = generate_event_selection_form(g.deployment)
    elif request.method == 'POST':
        form = generate_event_selection_form(g.deployment, request.form)

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


@route(core, '/location/<pk>', methods=['GET', 'POST'])
def location_edit(pk):
    template_name = 'core/location_edit.html'
    deployment = g.get('deployment')
    location = Location.objects.get_or_404(pk=pk, deployment=deployment)
    page_title = _('Edit location: %(name)s', name=location.name)

    if request.method == 'GET':
        form = generate_location_edit_form(location)
    else:
        form = generate_location_edit_form(location, request.form)

        if form.validate():
            form.populate_obj(location)
            location.save()

            return redirect(url_for('core.location_list'))

    return render_template(template_name, form=form, page_title=page_title)


@route(core, '/participants')
def participant_list_default():
    return participant_list(1)


@route(core, '/participants/<int:page>')
def participant_list(page=1):
    deployment = g.get('deployment')
    event = _get_event(session)
    page_title = _('Participants')
    template_name = 'frontend/participant_list.html'

    # load form context
    context = _get_form_context(deployment, event)

    participants = Participant.objects(
        deployment=deployment
    ).paginate(
        page=page,
        per_page=PAGE_SIZE
    )

    context.update(page_title=page_title, participants=participants)

    return render_template(
        template_name,
        **context
    )


@route(core, '/participant/<pk>', methods=['GET', 'POST'])
def participant_edit(pk):
    deployment = g.get('deployment')
    participant = Participant.objects.get_or_404(pk=pk, deployment=deployment)
    page_title = _(
        'Edit participant: %(participant_id)s',
        participant_id=participant.participant_id
    )
    template_name = 'core/participant_edit.html'

    if request.method == 'GET':
        form = generate_participant_edit_form(participant)
    else:
        form = generate_participant_edit_form(participant, request.form)

        if form.validate():
            participant.participant_id = form.participant_id.data
            participant.name = form.name.data
            participant.gender = form.gender.data
            participant.role = ParticipantRole.objects.with_id(form.role.data)
            participant.supervisor = Participant.objects.with_id(
                form.supervisor.data)
            participant.location = Location.objects.with_id(form.location.data)
            participant.partner = ParticipantPartner.objects.with_id(
                form.partner.data)
            participant.save()

            return redirect(url_for('core.participant_list'))

    return render_template(template_name, form=form, page_title=page_title)


@route(core, '/submissions/<form_id>', methods=['GET', 'POST'])
def submission_list(form_id):
    event = _get_event(session)
    deployment = g.get('deployment')
    form = Form.objects.get_or_404(deployment=deployment, pk=form_id)
    template_name = 'core/submission_list.html'

    queryset = Submission.objects(
        contributor__ne=None,
        created__lte=event.end_date,
        created__gte=event.start_date,
        deployment=deployment,
        form=form
    )

    if request.method == 'GET':
        filter_form = generate_submission_filter_form(form, event)
        return render_template(
            template_name,
            filter_form=filter_form,
            queryset=queryset
        )
        print queryset._query
    else:
        filter_form = generate_submission_filter_form(
            form, event, request.form)

        # process filter form
        for field in filter_form:
            if field.errors:
                continue

            # filter on groups
            if field.name.startswith('group_') and field.data:
                slug = field.name.split('_', 1)[1]
                try:
                    group = [grp.name for grp in form.groups if grp.slug == slug][0]
                except IndexError:
                    continue
                if field.data == '0':
                    continue
                elif field.data == '1':
                    queryset = queryset(
                        **{'completion__{}'.format(group): 'Partial'})
                elif field.data == '2':
                    queryset = queryset(
                        **{'completion__{}'.format(group): 'Missing'})
                elif field.data == '3':
                    queryset = queryset(
                        **{'completion__{}'.format(group): 'Complete'})
            else:
                # filter 'regular' fields
                if field.name == 'participant_id' and field.data:
                    # participant ID
                    participant = Participant.objects.get_or_404(
                        participant_id=field.data)
                    queryset = queryset(contributor=participant)
                elif field.name == 'location' and field.data:
                    # location
                    location = Location.objects.get_or_404(pk=field.data)
                    queryset = queryset.filter_in(location)
                elif field.name == 'sample' and field.data:
                    # sample
                    sample = Sample.objects.get_or_404(pk=field.data)
                    locations = Location.objects(samples=sample)
                    queryset = queryset(location__in=locations)

        print queryset._query
        return render_template(
            template_name,
            filter_form=filter_form,
            queryset=queryset
        )


def select_default_event(app, user):
    event = _get_event(session)
    session['event'] = unicode(event.id)


def clear_session(app, user):
    session.clear()


from flask.ext.login import user_logged_in, user_logged_out

user_logged_in.connect(select_default_event)
user_logged_out.connect(clear_session)
