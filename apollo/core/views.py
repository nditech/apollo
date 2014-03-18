from __future__ import absolute_import
from __future__ import unicode_literals
from logging import getLogger
from flask import (
    Blueprint, abort, flash, g, redirect, render_template,
    request, session, url_for
)
from flask.ext.babel import lazy_gettext as _
from flask.ext.security import login_required
from apollo.analyses.dashboard import get_coverage
from apollo.core.forms import (
    generate_dashboard_filter_form,
    generate_event_selection_form, generate_location_edit_form,
    generate_participant_edit_form, generate_submission_filter_form
)
from apollo.core.models import (
    Event, Form, Location, LocationType, Participant, ParticipantPartner,
    ParticipantRole, Sample, Submission
)

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


@core.app_errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403


@core.app_errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@core.app_errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


@core.route('/')
@core.route('/<group>')
@core.route('/<group>/location_type_id')
def index(group=None, location_type_id=None):
    # get variables from query params, or use (hopefully) sensible defaults
    deployment = g.get('deployment')
    if request.args.get('event'):
        event = Event.objects.with_id(request.args.get('event'))
        if event is None:
            abort(404)
    else:
        event = _get_event(session)

    if request.args.get('form'):
        form = Form.objects.with_id(request.args.get('form'))
    else:
        form = Form.objects(deployment=deployment, form_type='CHECKLIST',
                            events=event).first()

    if form is None:
        abort(404)

    page_title = _('Dashboard')
    template_name = 'core/dashboard.html'

    filter_form = generate_dashboard_filter_form(deployment, event)
    # only pick observer-created submissions
    queryset = Submission.objects(
        contributor__ne=None,
        deployment=deployment,
        form=form
    )

    # activate sample filter
    if request.args.get('sample'):
        sample = Sample.objects.get_or_404(request.args.get('sample'))
        locations = Location.objects(deployment=deployment, samples=sample)
        queryset = queryset.filter(location__in=locations)

    if group is None:
        data = get_coverage(queryset)
    else:
        if location_type_id is None:
            location_type = LocationType.get_root_for_event(event)
        else:
            location_type = LocationType.objects.get_or_404(
                pk=location_type_id)

        data = get_coverage(group, location_type)

    return render_template(
        template_name,
        data=data,
        filter_form=filter_form,
        page_title=page_title
    )


@core.route('/event', methods=['GET', 'POST'])
def event_selection():
    page_title = _('Select event')
    template_name = 'core/event_selection.html'

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

            session['event'] = event.id
            return redirect(url_for('core.index'))

    return render_template(template_name, form=form, page_title=page_title)


@core.route('/location/<pk>', methods=['GET', 'POST'])
def location_edit(pk):
    template_name = 'core/location_edit_2.html'
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


@core.route('/participants/<int:page>')
def participant_list(page=1):
    deployment = g.get('deployment')
    page_title = _('Participants')
    template_name = 'core/participant_list.html'

    participants = Participant.objects(
        deployment=deployment
    ).paginate(
        page=page,
        per_page=PAGE_SIZE
    )
    return render_template(
        template_name,
        page_title=page_title,
        participants=participants
    )


@core.route('/participant/<pk>', methods=['GET', 'POST'])
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


@core.route('/submissions')
def submission_list():
    return ''
