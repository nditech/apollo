# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from datetime import datetime
from flask import (
    Blueprint, flash, g, make_response, redirect, render_template, request,
    url_for, abort, current_app
)
from flask.ext.babel import lazy_gettext as _
from flask.ext.menu import register_menu
from flask.ext.security import current_user, login_required
from ..helpers import stash_file, load_source_file
from ..services import (
    events, locations, participants, participant_roles, participant_partners,
    user_uploads
)
from ..tasks import import_participants, send_message
from . import route, helpers, filters
from .forms import (
    generate_participant_edit_form, generate_participant_import_mapping_form,
    DummyForm, ParticipantUploadForm
)
from slugify import slugify_unicode

bp = Blueprint('participants', __name__, template_folder='templates',
               static_folder='static', static_url_path='/core/static')


@route(bp, '/participants', methods=['GET', 'POST'])
@register_menu(bp, 'participants', _('Participants'))
@login_required
def participant_list(page=1):
    page_title = _('Participants')
    template_name = 'frontend/participant_list.html'

    sortable_columns = {
        'id': 'participant_id',
        'name': 'name',
        'gen': 'gender'
    }

    extra_fields = g.deployment.participant_extra_fields or []

    for field in extra_fields:
        sortable_columns.update({field.name: field.name})

    queryset = participants.find()
    queryset_filter = filters.participant_filterset()(queryset, request.args)

    form = DummyForm(request.form)

    if request.form.get('action') == 'send_message':
        message = request.form.get('message', '')
        recipients = [participant.phone if participant.phone else ''
                      for participant in queryset_filter.qs]
        recipients.extend(current_app.config.get('MESSAGING_CC'))

        if message and recipients:
            send_message.delay(message, recipients)
            return 'OK'
        else:
            abort(400)

    '''if form.validate():
        # generate CSV of participants and force download
        # TODO: CSV is a sucky format for Unicode data.
        # It might break hard for non-ASCII characters.
        selected_participants = participants.find(
            pk__in=request.form.getlist('ids')
        )
        response = make_response(
            participants.export_list(selected_participants).csv
        )
        response.headers['Content-Disposition'] = 'attachment; ' + \
            'filename=participants.csv'
        response.headers['Content-Type'] = 'text/csv'
        return response'''

    if request.args.get('export'):
        # Export requested
        response = make_response(
            participants.export_list(queryset_filter.qs).xls
        )
        basename = slugify_unicode('participants %s' % (
            datetime.utcnow().strftime('%Y %m %d %H%M%S')))
        response.headers['Content-Disposition'] = 'attachment; ' + \
            'filename=%s.xls' % basename
        response.headers['Content-Type'] = 'application/vnd.ms-excel'
        return response
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


@route(bp, '/participant/<pk>', methods=['GET', 'POST'])
@login_required
def participant_edit(pk):
    participant = participants.get_or_404(pk=pk)
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
            participant.name = form.name.data
            participant.gender = form.gender.data
            participant.role = participant_roles.get(pk=form.role.data)
            if form.supervisor.data:
                participant.supervisor = participants.get(
                    pk=form.supervisor.data
                )
            else:
                participant.supervisor = None
            participant.location = locations.get(pk=form.location.data)
            participant.partner = participant_partners.get(
                pk=form.partner.data)
            participant.phone = form.phone.data
            participant.save()

            return redirect(url_for('participants.participant_list'))

    return render_template(template_name, form=form, page_title=page_title)


@route(bp, '/participants/import', methods=['GET', 'POST'])
@login_required
def participant_list_import():
    page_title = _('Import Participants')
    template_name = 'frontend/participant_import.html'

    if request.method == 'GET':
        form = ParticipantUploadForm()
        return render_template(template_name, form=form, page_title=page_title)
    else:
        form = ParticipantUploadForm(request.form)

        if not form.validate():
            return render_template(
                template_name,
                form=form,
                page_title=page_title
            )
        else:
            # get the actual object from the proxy
            user = current_user._get_current_object()
            event = events.get_or_404(pk=form.event.data)
            upload = stash_file(request.files['spreadsheet'], user, event)
            upload.save()

            return redirect(url_for(
                'participants.participant_headers',
                pk=unicode(upload.id)
            ))


@route(bp, '/participants/headers/<pk>', methods=['GET', 'POST'])
@login_required
def participant_headers(pk):
    user = current_user._get_current_object()

    # disallow processing other users' files
    upload = user_uploads.get_or_404(pk=pk, user=user)
    try:
        dataframe = load_source_file(upload.data)
    except Exception:
        # delete loaded file
        upload.data.delete()
        upload.delete()
        return render_template('frontend/invalid_import.html')

    deployment = g.deployment
    headers = dataframe.columns
    page_title = _('Map Participant Columns')
    template_name = 'frontend/participant_headers.html'

    if request.method == 'GET':
        form = generate_participant_import_mapping_form(deployment, headers)
        return render_template(template_name, form=form, page_title=page_title)
    else:
        form = generate_participant_import_mapping_form(
            deployment, headers, request.form)

        if not form.validate():
            return render_template(
                template_name,
                form=form,
                page_title=page_title
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

            # flash notification message and redirect
            flash(
                unicode(_('Your file is being processed. You will get an email when it is complete.')),
                category='task_begun'
            )
            return redirect(url_for('participants.participant_list'))
