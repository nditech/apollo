# -*- coding: utf-8 -*-
from datetime import datetime
import logging
import os
import re

from flask import (abort, Blueprint, current_app, flash, g, redirect,
                   render_template, request, Response, url_for,
                   stream_with_context)
from flask_babelex import lazy_gettext as _
from flask_menu import register_menu
from flask_restful import Api
from flask_security import current_user, login_required
from slugify import slugify_unicode

from apollo import models, services
from apollo.core import uploads
from apollo.frontend import helpers, permissions, route
from apollo.frontend.forms import (
    DummyForm, generate_participant_edit_form,
    generate_participant_import_mapping_form)
from apollo.helpers import load_source_file
from apollo.messaging.tasks import send_messages
from apollo.participants import api, filters, forms, tasks

phone_number_cleaner = re.compile(r'[^0-9]')

bp = Blueprint('participants', __name__, template_folder='templates',
               static_folder='static', static_url_path='/core/static')
logger = logging.getLogger(__name__)
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

admin_required = permissions.role('admin').require


def has_participant_set():
    return g.event.participant_set is not None


@route(bp, '/participants/set/<int:participant_set_id>',
       endpoint="participant_list_with_set", methods=['GET'])
@route(bp, '/participants', endpoint="participant_list", methods=['GET'])
@register_menu(
    bp, 'main.participants',
    _('Participants'),
    icon='<i class="glyphicon glyphicon-user"></i>',
    visible_when=lambda: permissions.view_participants.can()
    and has_participant_set(),
    order=5)
@permissions.view_participants.require(403)
@login_required
def participant_list(participant_set_id=0):
    if participant_set_id:
        participant_set = services.participant_sets.fget_or_404(
            id=participant_set_id)
        template_name = 'frontend/participant_list_with_set.html'
    else:
        participant_set = g.event.participant_set or abort(404)
        template_name = 'frontend/participant_list.html'

    page_title = _('Participants')

    sortable_columns = {
        'id': 'participant_id',
        'name': 'name',
        'gen': 'gender'
    }

    extra_fields = [field for field in participant_set.extra_fields
                    if field.visible_in_lists] \
        if participant_set.extra_fields else []
    location = None
    if request.args.get('location'):
        location = services.locations.find(
            id=request.args.get('location')).first()

    for field in extra_fields:
        sortable_columns.update({
            field.name: models.Participant.extra_data[field.name]})

    queryset = services.participants.find(
        participant_set_id=participant_set.id)

    # load the location set linked to the participant set
    location_set_id = participant_set.location_set_id
    filter_class = filters.participant_filterset(
        participant_set.id, location_set_id)
    queryset_filter = filter_class(queryset, request.args)

    form = DummyForm(request.form)

    if request.form.get('action') == 'send_message':
        message = request.form.get('message', '')
        recipients = [x for x in [participant.phone
                      if participant.phone else ''
                      for participant in queryset_filter.qs] if x is not '']
        recipients.extend(current_app.config.get('MESSAGING_CC'))

        if message and recipients and permissions.send_messages.can():
            send_messages.delay(g.event.id, message, recipients)
            return 'OK'
        else:
            abort(400)

    if request.args.get('export') and permissions.export_participants.can():
        # Export requested
        dataset = services.participants.export_list(queryset_filter.qs)
        basename = slugify_unicode('%s participants %s' % (
            participant_set.name.lower(),
            datetime.utcnow().strftime('%Y %m %d %H%M%S')))
        content_disposition = 'attachment; filename=%s.csv' % basename
        return Response(
            stream_with_context(dataset),
            headers={'Content-Disposition': content_disposition},
            mimetype="text/csv"
        )
    else:
        # request.args is immutable, so the .pop() call will fail on it.
        # using .copy() returns a mutable version of it.
        args = request.args.to_dict(flat=False)
        page_spec = args.pop('page', None) or [1]
        page = int(page_spec[0])
        if participant_set_id:
            args['participant_set_id'] = participant_set_id

        sort_by_arg = args.pop('sort_by', '')
        if isinstance(sort_by_arg, list):
            sort_param = sort_by_arg[0]
        else:
            sort_param = sort_by_arg
        sort_by = sortable_columns.get(sort_param, 'participant_id')
        subset = queryset_filter.qs.order_by(sort_by)

        # load form context
        context = dict(
            args=args,
            extra_fields=extra_fields,
            filter_form=queryset_filter.form,
            form=form,
            location=location,
            location_set_id=location_set_id,
            page_title=page_title,
            participant_set=participant_set,
            participant_set_id=participant_set.id,
            location_types=helpers.displayable_location_types(
                is_administrative=True),
            participants=subset.paginate(
                page=page, per_page=current_app.config.get('PAGE_SIZE'))
        )

        return render_template(
            template_name,
            **context
        )


@route(bp, '/participants/set/<int:participant_set_id>/performance',
       endpoint="participant_performance_list_with_set", methods=['GET'])
@route(bp, '/participants/performance',
       endpoint='participant_performance_list', methods=['GET'])
@permissions.view_participants.require(403)
@login_required
def participant_performance_list(participant_set_id=0):
    if participant_set_id:
        participant_set = services.participant_sets.fget_or_404(
            id=participant_set_id)
        template_name = 'frontend/participant_performance_list_with_set.html'
    else:
        participant_set = g.event.participant_set or abort(404)
        template_name = 'frontend/participant_performance_list.html'

    page_title = _('Participants Performance')

    sortable_columns = {
        'id': 'participant_id',
        'name': 'name',
        'gen': 'gender'
    }

    # extra_fields = g.deployment.participant_extra_fields or []
    extra_fields = []
    location = None
    if request.args.get('location'):
        location = services.locations.find(
            pk=request.args.get('location')).first()

    for field in extra_fields:
        sortable_columns.update({field.name: field.name})

    queryset = services.participants.find()
    sample_participant = queryset.first()
    if sample_participant:
        location_set_id = sample_participant.location.location_set_id
    else:
        location_set_id = None

    filter_class = filters.participant_filterset(
        participant_set.id, location_set_id)
    queryset_filter = filter_class(queryset, request.args)

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
        args = request.args.to_dict(flat=False)
        page_spec = args.pop('page', None) or [1]
        page = int(page_spec[0])
        if participant_set_id:
            args['participant_set_id'] = participant_set_id

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
            location_set_id=location_set_id,
            page_title=page_title,
            participant_set=participant_set,
            participant_set_id=participant_set.id,
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
    page_title = _('Participant Performance')
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
        phone_contact = next(filter(
            lambda p: phone == p.number, participant.phones), False)
        phone_contact.verified = True
        participant.save()
        submission.sender_verified = True
        submission.save()
        return 'OK'
    else:
        abort(400)


@route(bp, '/participant/<int:id>', methods=['GET', 'POST'])
@permissions.edit_participant.require(403)
@login_required
def participant_edit(id):
    participant = services.participants.fget_or_404(id=id)
    page_title = _(
        'Edit Participant · %(participant_id)s',
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
            participant_set = participant.participant_set
            participant.name = form.name.data
            participant.gender = form.gender.data
            if form.role.data:
                participant.role_id = services.participant_roles.fget_or_404(
                    id=form.role.data).id
            if form.supervisor.data:
                participant.supervisor_id = services.participants.find(
                    id=form.supervisor.data).first().id
            else:
                participant.supervisor_id = None
            if form.location.data:
                participant.location_id = services.locations.fget_or_404(
                    id=form.location.data).id
            if form.partner.data:
                participant.partner_id = \
                    services.participant_partners.fget_or_404(
                        id=form.partner.data).id
            else:
                participant.partner = None

            phone_number = phone_number_cleaner.sub('', form.phone.data)
            phone = services.phones.find(number=phone_number).first()
            if not phone:
                phone = services.phones.create(number=phone_number)
                participant_phone = services.participant_phones.create(
                    participant_id=participant.id, phone_id=phone.id,
                    verified=True)
            else:
                participant_phone = services.participant_phones.find(
                    phone_id=phone.id, participant_id=participant.id).first()
                if not participant_phone:
                    participant_phone = services.participant_phones.create(
                        participant_id=participant.id, phone_id=phone.id,
                        verified=True)
                else:
                    participant_phone.verified = True
                    participant_phone.save()

            participant.password = form.password.data
            if participant_set.extra_fields:
                for extra_field in participant_set.extra_fields:
                    field_data = getattr(
                        getattr(form, extra_field.name, object()), 'data', '')
                    setattr(participant, extra_field.name, field_data)
            participant.save()

            return redirect(url_for(
                'participants.participant_list',
                participant_set_id=participant_set.id))

    return render_template(
        template_name, form=form, page_title=page_title,
        participant=participant)


@route(bp, '/participants/set/<int:participant_set_id>/import',
       endpoint='participant_list_import_with_set', methods=['POST'])
@route(bp, '/participants/import',
       endpoint='participant_list_import', methods=['POST'])
@permissions.import_participants.require(403)
@login_required
def participant_list_import(participant_set_id=0):
    if participant_set_id:
        participant_set = services.participant_sets.fget_or_404(
            id=participant_set_id)
    else:
        participant_set = g.event.participant_set or abort(404)

    form = forms.ParticipantFileUploadForm(request.form)

    if not form.validate():
        return abort(400)
    else:
        # get the actual object from the proxy
        user = current_user._get_current_object()
        filename = uploads.save(request.files['spreadsheet'])
        upload = services.user_uploads.create(
            deployment_id=g.deployment.id, upload_filename=filename,
            user_id=user.id)

    if participant_set_id:
        return redirect(url_for(
            'participants.participant_headers_with_set',
            participant_set_id=participant_set.id,
            upload_id=upload.id)
        )
    else:
        return redirect(url_for(
            'participants.participant_headers',
            upload_id=upload.id)
        )


@route(bp, '/participants/set/<int:participant_set_id>/headers/'
       '<int:upload_id>', endpoint='participant_headers_with_set',
       methods=['GET', 'POST'])
@route(bp, '/participants/headers/<int:upload_id>',
       endpoint='participant_headers', methods=['GET', 'POST'])
@permissions.import_participants.require(403)
@login_required
def participant_headers(upload_id, participant_set_id=0):
    if participant_set_id:
        participant_set = services.participant_sets.fget_or_404(
            id=participant_set_id)
    else:
        participant_set = g.event.participant_set or abort(404)

    user = current_user._get_current_object()

    # disallow processing other users' files
    upload = services.user_uploads.fget_or_404(id=upload_id, user=user)
    filepath = uploads.path(upload.upload_filename)
    try:
        with open(filepath) as source_file:
            mapping_form_class = forms.make_import_mapping_form(
                source_file, participant_set)
    except Exception:
        # delete loaded file
        os.remove(filepath)
        upload.delete()
        return abort(400)

    form = mapping_form_class()
    template_name = 'frontend/participant_headers.html'

    if request.method == 'GET':
        return render_template(template_name, form=form)
    else:
        if not form.validate():
            return render_template(
                template_name,
                form=form
            )
        else:
            # get header mappings
            multi_column_fields = ('group', 'phone', 'sample')
            data = {fi: [] for fi in multi_column_fields}
            for field in form:
                if not field.data:
                    continue
                if field.data in multi_column_fields:
                    data[field.data].append(field.label.text)
                else:
                    data[field.data] = field.label.text

            for extra_field in participant_set.extra_fields:
                value = data.get(str(extra_field.id))
                if value is None:
                    continue
                data[extra_field.name] = value

            # invoke task asynchronously
            kwargs = {
                'upload_id': upload.id,
                'mappings': data,
                'participant_set_id': participant_set.id
            }
            tasks.import_participants.apply_async(kwargs=kwargs)

            if participant_set_id:
                return redirect(url_for(
                    'participants.participant_list_with_set',
                    participant_set_id=participant_set_id))
            else:
                return redirect(url_for('participants.participant_list'))


@route(bp, '/participants/purge', methods=['POST'])
@admin_required(403)
@login_required
def nuke_participants():
    event = g.event

    if event.participant_set_id:
        flash(
            str(_('Participants, Checklists, Critical Incidents and Messages'
                ' linked to this participant set are being deleted.')),
            category='task_begun'
        )
        tasks.nuke_participants.apply_async((event.participant_set_id,))

        return redirect(url_for(
            'participants.participant_list',
            participant_set_id=event.participant_set_id))

    return redirect(url_for('dashboard.index'))
