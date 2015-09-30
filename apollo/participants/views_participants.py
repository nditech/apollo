# -*- coding: utf-8 -*-
from __future__ import absolute_import

from datetime import datetime
from itertools import ifilter

from flask import (abort, Blueprint, current_app, g, redirect,
                   render_template, request, Response, url_for)
from flask.ext.babel import lazy_gettext as _
from flask.ext.menu import register_menu
from flask.ext.restful import Api
from flask.ext.security import current_user, login_required
from slugify import slugify_unicode

from apollo.frontend import filters, helpers, permissions, route
from apollo import services
from apollo.helpers import load_source_file, stash_file
from apollo.participants import api
from apollo.participants.tasks import import_participants
from apollo.messaging.tasks import send_messages
from apollo.frontend.forms import (
    DummyForm, generate_participant_edit_form,
    generate_participant_import_mapping_form,
    file_upload_form)

bp = Blueprint('participants', __name__, template_folder='templates',
               static_folder='static', static_url_path='/core/static')
participant_api = Api(bp)

participant_api.add_resource(
    api.ParticipantItemResource,
    '/api/participant/<participant_id>',
    endpoint='api.participant'
)
participant_api.add_resource(
    api.ParticipantListResource,
    '/api/participants/',
    endpoint='api.participants'
)


@route(bp, '/participants', methods=['GET', 'POST'])
@register_menu(
    bp, 'main.participants',
    _('Participants'),
    icon='<i class="glyphicon glyphicon-user"></i>',
    visible_when=lambda: permissions.view_participants.can(),
    order=5)
@permissions.view_participants.require(403)
@login_required
def participant_list(page=1):
    page_title = _('Participants')
    template_name = 'frontend/participant_list.html'

    sortable_columns = {
        'id': 'participant_id',
        'name': 'name',
        'gen': 'gender'
    }

    try:
        extra_fields = filter(
            lambda f: getattr(f, 'listview_visibility', False) is True,
            g.deployment.participant_extra_fields)
    except AttributeError:
        extra_fields = []
    location = None
    if request.args.get('location'):
        location = services.locations.find(
            pk=request.args.get('location')).first()

    for field in extra_fields:
        sortable_columns.update({field.name: field.name})

    queryset = services.participants.find()
    queryset_filter = filters.participant_filterset()(queryset, request.args)

    form = DummyForm(request.form)

    if request.form.get('action') == 'send_message':
        message = request.form.get('message', '')
        recipients = filter(
            lambda x: x is not '',
            [participant.phone if participant.phone else ''
                for participant in queryset_filter.qs])
        recipients.extend(current_app.config.get('MESSAGING_CC'))

        if message and recipients and permissions.send_messages.can():
            send_messages.delay(str(g.event.pk), message, recipients)
            return 'OK'
        else:
            abort(400)

    if request.args.get('export') and permissions.export_participants.can():
        # Export requested
        dataset = services.participants.export_list(queryset_filter.qs)
        basename = slugify_unicode('%s participants %s' % (
            g.event.name.lower(),
            datetime.utcnow().strftime('%Y %m %d %H%M%S')))
        content_disposition = 'attachment; filename=%s.csv' % basename
        return Response(
            dataset, headers={'Content-Disposition': content_disposition},
            mimetype="text/csv"
        )
    else:
        # request.args is immutable, so the .pop() call will fail on it.
        # using .copy() returns a mutable version of it.
        args = request.args.copy()
        page = int(args.pop('page', '1'))

        sort_by = sortable_columns.get(
            args.pop('sort_by', ''), 'participant_id')
        subset = queryset_filter.qs.order_by(sort_by)

        # load form context
        context = dict(
            args=args,
            extra_fields=extra_fields,
            filter_form=queryset_filter.form,
            form=form,
            location=location,
            page_title=page_title,
            location_types=helpers.displayable_location_types(
                is_administrative=True),
            participants=subset.paginate(
                page=page, per_page=current_app.config.get('PAGE_SIZE'))
        )

        return render_template(
            template_name,
            **context
        )


@route(bp, '/participants/performance', methods=['GET', 'POST'])
@permissions.view_participants.require(403)
@login_required
def participant_performance_list(page=1):
    page_title = _('Participants Performance')
    template_name = 'frontend/participant_performance_list.html'

    sortable_columns = {
        'id': 'participant_id',
        'name': 'name',
        'gen': 'gender'
    }

    extra_fields = g.deployment.participant_extra_fields or []
    location = None
    if request.args.get('location'):
        location = services.locations.find(
            pk=request.args.get('location')).first()

    for field in extra_fields:
        sortable_columns.update({field.name: field.name})

    queryset = services.participants.find()
    queryset_filter = filters.participant_filterset()(queryset, request.args)

    form = DummyForm(request.form)

    if request.form.get('action') == 'send_message':
        message = request.form.get('message', '')
        recipients = [participant.phone if participant.phone else ''
                      for participant in queryset_filter.qs]
        recipients.extend(current_app.config.get('MESSAGING_CC'))

        if message and recipients and permissions.send_messages.can():
            send_messages.delay(str(g.event.pk), message, recipients)
            return 'OK'
        else:
            abort(400)

    if request.args.get('export') and permissions.export_participants.can():
        # Export requested
        dataset = services.participants.export_performance_list(
            queryset_filter.qs)
        basename = slugify_unicode('%s participants performance %s' % (
            g.event.name.lower(),
            datetime.utcnow().strftime('%Y %m %d %H%M%S')))
        content_disposition = 'attachment; filename=%s.csv' % basename
        return Response(
            dataset, headers={'Content-Disposition': content_disposition},
            mimetype="text/csv"
        )
    else:
        # request.args is immutable, so the .pop() call will fail on it.
        # using .copy() returns a mutable version of it.
        args = request.args.copy()
        page = int(args.pop('page', '1'))

        sort_by = sortable_columns.get(
            args.pop('sort_by', ''), 'participant_id')
        subset = queryset_filter.qs.order_by(sort_by)

        # load form context
        context = dict(
            args=args,
            extra_fields=extra_fields,
            filter_form=queryset_filter.form,
            form=form,
            location=location,
            page_title=page_title,
            location_types=helpers.displayable_location_types(
                is_administrative=True),
            participants=subset.paginate(
                page=page, per_page=current_app.config.get('PAGE_SIZE'))
        )

        return render_template(
            template_name,
            **context
        )


@route(bp, '/participant/performance/<pk>')
@permissions.view_participants.require(403)
@login_required
def participant_performance_detail(pk):
    participant = services.participants.get_or_404(id=pk)
    page_title = _(u'Participant Performance')
    template_name = 'frontend/participant_performance_detail.html'
    messages = services.messages.find(
        participant=participant,
        direction='IN'
    ).order_by('received')

    context = {
        'participant': participant,
        'messages': messages,
        'page_title': page_title
    }

    return render_template(template_name, **context)


@route(bp, '/participant/phone/verify', methods=['POST'])
@permissions.edit_participant.require(403)
@login_required
def participant_phone_verify():
    if request.is_xhr:
        contributor = request.form.get('contributor')
        phone = request.form.get('phone')
        submission_id = request.form.get('submission')

        submission = services.submissions.get_or_404(id=submission_id)
        participant = services.participants.get_or_404(id=contributor)
        phone_contact = next(ifilter(
            lambda p: phone == p.number, participant.phones), False)
        phone_contact.verified = True
        participant.save()
        submission.sender_verified = True
        submission.save()
        return 'OK'
    else:
        abort(400)


@route(bp, '/participant/<pk>', methods=['GET', 'POST'])
@permissions.edit_participant.require(403)
@login_required
def participant_edit(pk):
    participant = services.participants.get_or_404(pk=pk)
    page_title = _(
        u'Edit Participant · %(participant_id)s',
        participant_id=participant.participant_id
    )

    if request.is_xhr:
        template_name = 'frontend/participant_edit_modal.html'
    else:
        template_name = 'frontend/participant_edit.html'

    if request.method == 'GET':
        form = generate_participant_edit_form(participant)
    else:
        form = generate_participant_edit_form(participant, request.form)

        if form.validate():
            # participant.participant_id = form.participant_id.data
            participant.name = form.name.data
            participant.gender = form.gender.data
            participant.role = services.participant_roles.get_or_404(
                pk=form.role.data)
            if form.supervisor.data:
                participant.supervisor = services.participants.get(
                    pk=form.supervisor.data
                )
            else:
                participant.supervisor = None
            if form.location.data:
                participant.location = services.locations.get_or_404(
                    pk=form.location.data)
            if form.partner.data:
                participant.partner = services.participant_partners.get_or_404(
                    pk=form.partner.data)
            else:
                participant.partner = None
            participant.phone = form.phone.data
            participant.password = form.password.data
            for extra_field in g.deployment.participant_extra_fields:
                field_data = getattr(
                    getattr(form, extra_field.name, object()), 'data', '')
                setattr(participant, extra_field.name, field_data)
            participant.save()

            print 'redirecting'

            return redirect(url_for('participants.participant_list'))

    return render_template(
        template_name, form=form, page_title=page_title,
        participant=participant)


@route(bp, '/participants/import', methods=['POST'])
@permissions.import_participants.require(403)
@login_required
def participant_list_import():
    form = file_upload_form(request.form)

    if not form.validate():
        return abort(400)
    else:
        # get the actual object from the proxy
        user = current_user._get_current_object()
        event = services.events.get_or_404(pk=form.event.data)
        upload = stash_file(request.files['spreadsheet'], user, event)
        upload.save()

        return redirect(url_for(
            'participants.participant_headers',
            pk=unicode(upload.id)
        ))


@route(bp, '/participants/headers/<pk>', methods=['GET', 'POST'])
@permissions.import_participants.require(403)
@login_required
def participant_headers(pk):
    user = current_user._get_current_object()

    # disallow processing other users' files
    upload = services.user_uploads.get_or_404(pk=pk, user=user)
    try:
        dataframe = load_source_file(upload.data)
    except Exception:
        # delete loaded file
        upload.data.delete()
        upload.delete()
        return abort(400)

    deployment = g.deployment
    headers = dataframe.columns
    template_name = 'frontend/participant_headers.html'

    if request.method == 'GET':
        form = generate_participant_import_mapping_form(deployment, headers)
        return render_template(template_name, form=form)
    else:
        form = generate_participant_import_mapping_form(
            deployment, headers, request.form)

        if not form.validate():
            return render_template(
                template_name,
                form=form
            )
        else:
            # get header mappings
            data = form.data.copy()

            # phone_header = data.pop('phone')
            # group_header = data.pop('group')
            # mappings = {v: k for k, v in data.iteritems() if v}
            # mappings.update(phone=phone_header)
            # mappings.update(group=group_header)

            # invoke task asynchronously
            kwargs = {
                'upload_id': unicode(upload.id),
                'mappings': data
            }
            import_participants.apply_async(kwargs=kwargs)

            return redirect(url_for('participants.participant_list'))
