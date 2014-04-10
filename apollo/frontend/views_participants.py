# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from flask import (
    Blueprint, redirect, render_template, request, url_for
)
from flask.ext.babel import lazy_gettext as _
from flask.ext.menu import register_menu
from flask.ext.security import current_user, login_required
from ..helpers import stash_file
from ..participants.tasks import load_source_file
from ..services import (
    events, locations, participants, participant_roles, participant_partners,
    user_uploads
)
from ..tasks import import_participants
from . import route
from .filters import ParticipantFilterSet
from .forms import (
    generate_participant_edit_form, generate_participant_import_mapping_form,
    ParticipantUploadForm
)

PAGE_SIZE = 25
bp = Blueprint('participants', __name__, template_folder='templates',
               static_folder='static', static_url_path='/core/static')


@route(bp, '/participants')
@register_menu(bp, 'participants', _('Participants'))
@login_required
def participant_list(page=1):
    page_title = _('Participants')
    queryset = participants.find()
    queryset_filter = ParticipantFilterSet(queryset, request.args)

    template_name = 'frontend/participant_list.html'

    # request.args is immutable, so the .pop() call will fail on it.
    # using .copy() returns a mutable version of it.
    args = request.args.copy()
    page = int(args.pop('page', '1'))

    # load form context
    context = {}

    pager = queryset_filter.qs.paginate(page=page, per_page=PAGE_SIZE)

    context.update(
        args=args,
        filter_form=queryset_filter.form,
        page_title=page_title,
        participants=pager
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
        'Edit participant: %(participant_id)s',
        participant_id=participant.participant_id
    )
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
            participant.supervisor = participants.get(pk=form.supervisor.data)
            participant.location = locations.get(pk=form.location.data)
            participant.partner = participant_partners.get(
                pk=form.partner.data)
            participant.save()

            return redirect(url_for('participants.participant_list'))

    return render_template(template_name, form=form, page_title=page_title)


@route(bp, '/participants/import', methods=['GET', 'POST'])
@login_required
def participant_list_import():
    page_title = _('Import participants')
    template_name = 'frontend/participant_import.html'

    if request.method == 'GET':
        form = ParticipantUploadForm()
        return render_template(template_name, form=form, page_title=page_title)
    else:
        form = ParticipantUploadForm(request.form)

        if not form.validate():
            print form.errors
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

    headers = dataframe.columns
    page_title = _('Map participant columns')
    template_name = 'frontend/participant_headers.html'

    if request.method == 'GET':
        form = generate_participant_import_mapping_form(headers)
        return render_template(template_name, form=form, page_title=page_title)
    else:
        form = generate_participant_import_mapping_form(headers, request.form)

        if not form.validate():
            return render_template(
                template_name,
                form=form,
                page_title=page_title
            )
        else:
            # get header mappings
            phone_header = form.data.get('phone')
            mappings = {v: k for k, v in form.data.iteritems()}
            mappings.update(phone=phone_header)
            # invoke task asynchronously
            kwargs = {
                'upload_id': unicode(upload.id),
                'mappings': mappings
            }
            import_participants.apply_async(kwargs=kwargs)
            return render_template('frontend/import_started.html')
