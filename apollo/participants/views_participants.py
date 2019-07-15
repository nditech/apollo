# -*- coding: utf-8 -*-
from datetime import datetime
import logging
import os
import re

from flask import (abort, Blueprint, current_app, g, redirect,
                   render_template, request, Response, url_for,
                   stream_with_context)
from flask_babelex import lazy_gettext as _
from flask_menu import register_menu
from flask_security import current_user, login_required
from slugify import slugify_unicode

from apollo import models, services, utils
from apollo.core import docs, sentry, uploads
from apollo.frontend import helpers, permissions, route
from apollo.frontend.forms import generate_participant_edit_form
from apollo.messaging.tasks import send_messages
from apollo.participants import filters, forms, tasks
from apollo.participants.api import views as api_views

from .models import Participant, ParticipantSet, ParticipantRole
from .models import ParticipantPartner, PhoneContact
from .models import ParticipantTranslations
from ..locations.models import Location
from ..submissions.models import Submission
from ..users.models import UserUpload

from sqlalchemy import desc, func, text


phone_number_cleaner = re.compile(r'[^0-9]')

bp = Blueprint('participants', __name__, template_folder='templates',
               static_folder='static', static_url_path='/core/static')
logger = logging.getLogger(__name__)

bp.add_url_rule(
    '/api/participants/<int:participant_id>',
    view_func=api_views.ParticipantItemResource.as_view(
        'api_participant_item'))
bp.add_url_rule(
    '/api/participants/',
    view_func=api_views.ParticipantListResource.as_view(
        'api_participant_list'))

docs.register(
    api_views.ParticipantItemResource, 'participants.api_participant_item')
docs.register(
    api_views.ParticipantListResource, 'participants.api_participant_list')

admin_required = permissions.role('admin').require


def has_participant_set():
    return g.event.participant_set is not None


@route(
    bp, '/participants', endpoint="participant_list",
    methods=['GET', 'POST'])
@register_menu(
    bp, 'main.participants',
    _('Participants'),
    icon='<i class="glyphicon glyphicon-user"></i>',
    visible_when=lambda: permissions.view_participants.can()
    and has_participant_set(),
    order=5)
@login_required
@permissions.view_participants.require(403)
def participant_list(participant_set_id=0, view=None):
    if participant_set_id:
        participant_set = ParticipantSet.query.filter(
            ParticipantSet.id == participant_set_id).first_or_404()
        template_name = 'admin/participant_list.html'
        breadcrumbs = [
            {
                'url': url_for('participantset.index_view'),
                'text': _('Participant Sets')
            },
            participant_set.name, _('Participants')]
    else:
        participant_set = g.event.participant_set or abort(404)
        template_name = 'frontend/participant_list.html'
        breadcrumbs = [_('Participants')]

    extra_fields = [field for field in participant_set.extra_fields
                    if field.visible_in_lists] \
        if participant_set.extra_fields else []

    location = None
    if request.args.get('location'):
        location = Location.query.filter(
            Location.id == request.args.get('location')).first()

    queryset = Participant.query.select_from(
        Participant, ParticipantTranslations).filter(
        Participant.participant_set_id == participant_set.id)

    # load the location set linked to the participant set
    location_set_id = participant_set.location_set_id
    filter_class = filters.participant_filterset(
        participant_set.id, location_set_id)
    queryset_filter = filter_class(queryset, request.args)

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

    # the following section defines the queryset for the participants
    # to be retrieved. due to the fact that we do specialized sorting
    # the queryset will depend heavily on what is being sorted.
    if (
        request.args.get('sort_by') == 'location' and
        request.args.get('sort_value')
    ):
        # when sorting based on location, we generally want to be able
        # to sort participants based on a specific administrative division.
        # since we store the hierarchical structure in a separate table
        # we not only have to retrieve the table for the location data but
        # also join it based on results in the location hierarchy.

        # start out by getting all the locations (as a subquery) in a
        # particular division.

        division = models.Location.query.with_entities(
            models.Location.id).filter(
                models.Location.location_type_id ==
                request.args.get('sort_value')
            ).subquery()
        # next is we retrieve all the descendant locations for all the
        # locations in that particular administrative division making sure
        # to retrieve the name translations which would be used in sorting
        # the participants when the time comes.
        descendants = models.LocationPath.query.join(
                models.Location,
                models.Location.id == models.LocationPath.ancestor_id
            ).with_entities(
                models.Location.name_translations,
                models.LocationPath.descendant_id
            ).filter(
                models.LocationPath.ancestor_id.in_(division)
            ).subquery()

        # now we defined the actual queryset using the subqueries above
        # taking note to group by the translation name which essentially
        # is the division name.
        queryset = models.Participant.query.select_from(
            models.Participant, models.Location,
            func.jsonb_each_text(
                descendants.c.name_translations).alias('translation')
        ).filter(
            models.Participant.participant_set_id == participant_set.id
        ).join(
            models.Location,
            models.Participant.location_id == models.Location.id
        ).outerjoin(
            descendants,
            descendants.c.descendant_id == models.Participant.location_id
        ).group_by(
            text('translation.value'), models.Participant.id
        )
    elif request.args.get('sort_by') == 'phone':
        queryset = models.Participant.query.filter(
            models.Participant.participant_set_id == participant_set.id
        ).join(
            models.Location,
            models.Participant.location_id == models.Location.id
        ).join(
            models.PhoneContact,
            models.PhoneContact.participant_id == models.Participant.id
        )
    else:
        queryset = models.Participant.query.select_from(
            models.Participant, ParticipantTranslations,
            models.Location,
            func.jsonb_each_text(models.Location.name_translations).alias(
                'translation'),
            func.jsonb_each_text(models.Participant.name_translations).alias(
                'participant_name'), models.ParticipantRole,
            models.ParticipantPartner
        ).filter(
            models.Participant.participant_set_id == participant_set.id
        ).join(
            models.Location,
            models.Participant.location_id == models.Location.id
        ).outerjoin(
            models.ParticipantRole,
            models.Participant.role_id == models.ParticipantRole.id
        ).outerjoin(
            models.ParticipantPartner,
            models.Participant.partner_id == models.ParticipantPartner.id
        )

    if request.args.get('sort_by') == 'id':
        if request.args.get('sort_direction') == 'desc':
            queryset = queryset.order_by(
                desc(models.Participant.participant_id))
        else:
            queryset = queryset.order_by(
                models.Participant.participant_id)
    elif request.args.get('sort_by') in ('location_name', 'location',):
        if request.args.get('sort_direction') == 'desc':
            queryset = queryset.order_by(
                desc(text('translation.value')))
        else:
            queryset = queryset.order_by(text('translation.value'))
    elif request.args.get('sort_by') == 'name':
        if request.args.get('sort_direction') == 'desc':
            queryset = queryset.order_by(
                desc(text('participant_name.value')))
        else:
            queryset = queryset.order_by(text('participant_name.value'))
    elif request.args.get('sort_by') == 'phone':
        if request.args.get('sort_direction') == 'desc':
            queryset = queryset.order_by(
                desc(models.PhoneContact.number))
        else:
            queryset = queryset.order_by(
                models.PhoneContact.number)
    elif request.args.get('sort_by') == 'gen':
        if request.args.get('sort_direction') == 'desc':
            queryset = queryset.order_by(
                desc(models.Participant.gender))
        else:
            queryset = queryset.order_by(
                models.Participant.gender)
    elif request.args.get('sort_by') == 'role':
        if request.args.get('sort_direction') == 'desc':
            queryset = queryset.order_by(
                desc(models.ParticipantRole.name))
        else:
            queryset = queryset.order_by(
                models.ParticipantRole.name)
    elif request.args.get('sort_by') == 'org':
        if request.args.get('sort_direction') == 'desc':
            queryset = queryset.order_by(
                desc(models.ParticipantPartner.name))
        else:
            queryset = queryset.order_by(
                models.ParticipantPartner.name)
    else:
        queryset = queryset.order_by(
            models.Location.code,
            models.Participant.participant_id)

    # request.args is immutable, so the .pop() call will fail on it.
    # using .copy() returns a mutable version of it.
    args = request.args.to_dict(flat=False)
    page = int(args.pop('page', [1])[0])
    if participant_set_id:
        args['participant_set_id'] = participant_set_id

    queryset_filterset = filter_class(queryset, request.args)
    filter_form = queryset_filterset.form

    if request.form.get('action') == 'send_message':
        message = request.form.get('message', '')
        recipients = [x for x in [participant.primary_phone
                                  if participant.primary_phone else ''
                                  for participant in queryset_filterset.qs]
                      if x != '']
        recipients.extend(current_app.config.get('MESSAGING_CC'))

        if message and recipients and permissions.send_messages.can():
            send_messages.delay(g.event.id, message, recipients)
            return 'OK'
        else:
            abort(400)

    # load form context
    context = dict(
        args=args,
        extra_fields=extra_fields,
        filter_form=filter_form,
        location=location,
        location_set_id=location_set_id,
        breadcrumbs=breadcrumbs,
        participant_set=participant_set,
        participant_set_id=participant_set.id,
        location_types=helpers.displayable_location_types(
            is_administrative=True, location_set_id=location_set_id),
        participants=queryset_filterset.qs.paginate(
            page=page, per_page=current_app.config.get('PAGE_SIZE'))
    )

    if view:
        return view.render(
            template_name,
            **context
        )
    else:
        return render_template(
            template_name,
            **context
        )


@route(bp, '/participant/phone/verify', methods=['POST'])
@login_required
@permissions.edit_participant.require(403)
def toggle_phone_verification():
    """
    Toggles phone verification status for a participant phone
    and submission
    """
    if request.is_xhr:
        participant_id = request.form.get('participant')
        phone = request.form.get('phone')
        submission_id = request.form.get('submission')

        submission = Submission.query.get_or_404(submission_id)
        participant = Participant.query.get_or_404(participant_id)
        phone_contact = PhoneContact.query.filter(
            PhoneContact.participant==participant,
            PhoneContact.number==phone).first()
        phone_contact.verified = not phone_contact.verified
        submission.sender_verified = phone_contact.verified
        phone_contact.save()
        submission.save()
        return '1' if phone_contact.verified else '0'
    else:
        abort(400)


@route(bp, '/participant/<int:id>',
       endpoint='participant_edit', methods=['GET', 'POST'])
@login_required
@permissions.edit_participant.require(403)
def participant_edit(id, participant_set_id=0, view=None):
    participant = Participant.query.get_or_404(id)
    breadcrumbs = [
        _('Participants'),
        _('Edit Participant'),
        participant.participant_id
    ]

    template_name = 'frontend/participant_edit.html'

    if request.method == 'GET':
        form = generate_participant_edit_form(participant)
    else:
        form = generate_participant_edit_form(participant, request.form)

        if form.validate():
            # participant.participant_id = form.participant_id.data
            participant_set = participant.participant_set
            deployment = participant_set.deployment
            name_translations = {}
            for locale in deployment.locale_codes:
                field_name = f'name_{locale}'
                name_translations[locale] = getattr(form, field_name).data
            participant.name_translations = name_translations
            participant.gender = form.gender.data
            if form.role.data:
                participant.role_id = ParticipantRole.query.get_or_404(
                    form.role.data).id
            if form.supervisor.data:
                participant.supervisor = form.supervisor.data
            else:
                participant.supervisor = None
            if form.location.data:
                participant.location = form.location.data
            if form.partner.data:
                participant.partner_id = ParticipantPartner.query.get_or_404(
                    form.partner.data).id
            else:
                participant.partner = None

            phone_number = phone_number_cleaner.sub('', form.phone.data)
            # do we have a phone number like this in the database?
            phone = PhoneContact.query.filter_by(
                number=phone_number, participant_id=id).first()

            if phone is None:
                # no, overwrite the primary phone,
                # or create a new primary phone
                primary_num = participant.primary_phone
                phone = PhoneContact.query.filter_by(
                    number=primary_num, participant_id=id, verified=True
                ).first()
                if phone:
                    phone.number = phone_number
                else:
                    phone = PhoneContact(
                        number=phone_number, participant_id=id, verified=True)
            else:
                # yes, so update the verified attribute, as the updated
                # attribute is automatically updated.
                # this will then  become the new primary number
                # (primary is the most recently updated and
                # verified phone number)
                phone.verified = True
            phone.save()

            participant.password = form.password.data
            if participant_set.extra_fields:
                extra_data = {}
                for extra_field in participant_set.extra_fields:
                    field_data = getattr(
                        getattr(form, extra_field.name, object()), 'data', '')
                    if field_data != '':
                        extra_data[extra_field.name] = field_data

                participant.extra_data = extra_data

            participant.save()

            if participant_set_id:
                return redirect(url_for(
                    'participants.participant_list_with_set',
                    participant_set_id=participant_set.id))
            else:
                return redirect(url_for('participants.participant_list'))

    if view:
        return view.render(
            template_name, form=form, breadcrumbs=breadcrumbs,
            participant_set_id=participant_set_id,
            participant=participant)
    else:
        return render_template(
            template_name, form=form, breadcrumbs=breadcrumbs,
            participant_set_id=participant_set_id,
            participant=participant)


@route(bp, '/participants/import',
       endpoint='participant_list_import', methods=['POST'])
@login_required
@permissions.import_participants.require(403)
def participant_list_import(participant_set_id=0):
    if participant_set_id:
        participant_set = ParticipantSet.query.get_or_404(participant_set_id)
    else:
        participant_set = g.event.participant_set or abort(404)

    form = forms.ParticipantFileUploadForm(request.form)

    if not form.validate():
        return abort(400)
    else:
        # get the actual object from the proxy
        user = current_user._get_current_object()
        upload_file = utils.strip_bom_header(request.files['spreadsheet'])
        filename = uploads.save(upload_file)
        upload = services.user_uploads.create(
            deployment_id=g.deployment.id, upload_filename=filename,
            user_id=user.id)

    if participant_set_id:
        return redirect(url_for(
            'participantset.participants_headers',
            participant_set_id=participant_set.id,
            upload_id=upload.id)
        )
    else:
        return redirect(url_for(
            'participants.participant_headers',
            upload_id=upload.id)
        )


@route(bp, '/participants/headers/<int:upload_id>',
       endpoint='participant_headers', methods=['GET', 'POST'])
@login_required
@permissions.import_participants.require(403)
def participant_headers(upload_id, participant_set_id=0, view=None):
    if participant_set_id:
        participant_set = ParticipantSet.query.get_or_404(participant_set_id)
    else:
        participant_set = g.event.participant_set or abort(404)

    user = current_user._get_current_object()

    # disallow processing other users' files
    upload = UserUpload.query.filter(
        UserUpload.id == upload_id,
        UserUpload.user == user).first_or_404()
    filepath = uploads.path(upload.upload_filename)
    try:
        with open(filepath, 'rb') as source_file:
            mapping_form_class = forms.make_import_mapping_form(
                source_file, participant_set)
    except Exception:
        # delete loaded file
        os.remove(filepath)
        upload.delete()
        sentry.captureException()
        return abort(400)

    form = mapping_form_class()
    template_name = 'frontend/participant_headers.html'

    if request.method == 'GET':
        return render_template(template_name, form=form)
    else:
        if not form.validate():
            error_msgs = []
            for key in form.errors:
                for msg in form.errors[key]:
                    error_msgs.append(msg)
            if view:
                return view.render(
                    'frontend/participant_headers_errors.html',
                    error_msgs=error_msgs), 400
            else:
                return render_template(
                    'frontend/participant_headers_errors.html',
                    error_msgs=error_msgs), 400
        else:
            if 'X-Validate' not in request.headers:
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
                    'participantset.participants_list',
                    participant_set_id=participant_set_id))
            else:
                return redirect(url_for('participants.participant_list'))


@route(bp, '/participant/call', methods=['POST'])
@login_required
def log_call():
    """
    Adds a call log for the participant
    """
    if request.is_xhr:
        participant_id = request.form.get('participant')
        description = request.form.get('description')

        participant = Participant.query.get_or_404(participant_id)
        user = current_user._get_current_object()
        contact = models.ContactHistory(
            participant=participant,user=user, description=description)

        contact.save()
        return '1'
    else:
        abort(400)
