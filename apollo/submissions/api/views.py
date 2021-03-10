# -*- coding: utf-8 -*-
import json
from http import HTTPStatus
from uuid import uuid4

from flask import g, jsonify, request
from flask_apispec import MethodResource, marshal_with, use_kwargs
from flask_babelex import gettext
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy.orm.exc import NoResultFound
from webargs import fields

from apollo.api.common import BaseListResource
from apollo.api.decorators import protect
from apollo.core import csrf, db
from apollo.deployments.models import Event
from apollo.formsframework.forms import filter_form, filter_participants
from apollo.frontend.helpers import DictDiffer
from apollo.odk.utils import make_message_text
from apollo.participants.models import Participant
from apollo.services import messages
from apollo.submissions.api.schema import SubmissionSchema
from apollo.submissions.models import (
    Submission, SubmissionImageAttachment, SubmissionVersion)
from apollo.utils import current_timestamp


def update_submission_version(submission):
    submission = Submission.query.get(submission.id)
    db.session.refresh(submission)

    # save actual version data
    data_fields = submission.form.tags
    version_data = {
        k: submission.data.get(k)
        for k in data_fields if k in submission.data}

    if submission.form.form_type == 'INCIDENT':
        if submission.incident_status:
            version_data['status'] = submission.incident_status.code

        if submission.incident_description:
            version_data['description'] = submission.incident_description

    # get previous version
    previous = SubmissionVersion.query.filter(
        SubmissionVersion.submission == submission).order_by(
            SubmissionVersion.timestamp.desc()).first()

    if previous:
        diff = DictDiffer(version_data, previous.data)

        # don't do anything if the data wasn't changed
        if not diff.added() and not diff.removed() and not diff.changed():
            return

    channel = 'PWA'
    identity = submission.participant.participant_id

    version = SubmissionVersion(
        submission_id=submission.id,
        data=version_data,
        timestamp=current_timestamp(),
        channel=channel,
        identity=identity,
        deployment_id=submission.deployment_id
    )
    version.save()


@marshal_with(SubmissionSchema)
@use_kwargs({'event_id': fields.Int()}, locations=['query'])
class SubmissionItemResource(MethodResource):
    @protect
    def get(self, submission_id, **kwargs):
        deployment = getattr(g, 'deployment', None)

        event_id = kwargs.get('event_id')
        if event_id is None:
            event = getattr(g, 'event', None)
            event_id = event.id if event else None

        deployment_id = deployment.id if deployment else None

        submission = Submission.query.filter_by(
            deployment_id=deployment_id, event_id=event_id,
            id=submission_id
        ).first_or_404()

        return submission


@use_kwargs({'event_id': fields.Int(), 'form_id': fields.Int(required=True),
            'submission_type': fields.Str()}, locations=['query'])
class SubmissionListResource(BaseListResource):
    schema = SubmissionSchema()

    @protect
    def get_items(self, **kwargs):
        deployment = getattr(g, 'deployment', None)
        deployment_id = deployment.id if deployment else None

        form_id = kwargs.get('form_id')

        event_id = kwargs.get('event_id')
        if not event_id:
            event = getattr(g, 'event', None)
            event_id = event.id if event else None

        query = Submission.query.filter_by(
            deployment_id=deployment_id,
            event_id=event_id,
            form_id=form_id
        )

        submission_type = kwargs.get('submission_type')
        if submission_type:
            query = query.filter_by(submission_type=submission_type)

        return query


@csrf.exempt
@jwt_required()
def submission():
    try:
        request_data = json.loads(request.form.get('submission'))
    except Exception:
        response = {
            'message': gettext('Invalid data sent'),
            'status': 'error'
        }

        return jsonify(response), HTTPStatus.BAD_REQUEST

    form_id = request_data.get('form')
    form_serial = request_data.get('serial')
    payload = request_data.get('data')
    participant_uuid = get_jwt_identity()

    form = filter_form(form_id)
    if form is None:
        response = {
            'message': gettext('Invalid form'),
            'status': 'error'
        }

        return jsonify(response), HTTPStatus.BAD_REQUEST

    try:
        participant = Participant.query.filter_by(uuid=participant_uuid).one()
    except NoResultFound:
        response = {
            'message': gettext('Invalid participant'),
            'status': 'error'
        }

        return jsonify(response), HTTPStatus.BAD_REQUEST

    participant = filter_participants(form, participant.participant_id)
    if participant is None:
        response = {
            'message': gettext('Invalid participant'),
            'status': 'error'
        }

        return jsonify(response), HTTPStatus.BAD_REQUEST

    # validate payload
    schema_class = form.create_schema()
    data, errors = schema_class().load(payload)
    if errors:
        response = {
            'message': gettext('Invalid value(s) for: %(fields)s',
                               fields=','.join(sorted(errors.keys()))),
            'status': 'error'
        }

        return jsonify(response), HTTPStatus.BAD_REQUEST

    current_event = getattr(g, 'event', Event.default())
    current_events = Event.overlapping_events(current_event)
    event_ids = current_events.with_entities(Event.id)

    if form.form_type == 'CHECKLIST':
        # when searching for the submission, take into cognisance
        # that the submission may be in one of several concurrent
        # events
        submission = Submission.query.filter(
            Submission.participant == participant,
            Submission.form == form,
            Submission.submission_type == 'O',
            Submission.event_id.in_(event_ids)
        ).first()

    elif form.form_type == 'SURVEY':
        submission = Submission.query.filter(
            Submission.participant == participant,
            Submission.form == form,
            Submission.submission_type == 'O',
            Submission.serial_no == form_serial,
            Submission.event_id.in_(event_ids)
        ).first()
    else:
        # the submission event is determined by taking the intersection
        # of form events, participant events and concurrent events
        # and taking the last event ordered by descending end date
        event = current_events.join(Event.forms).filter(
            Event.forms.contains(form),
            Event.participant_set_id == participant.participant_set_id
        ).order_by(Event.end.desc()).first()

        if event is None:
            submission = None
        else:
            submission = Submission(
                submission_type='O',
                form=form,
                participant=participant,
                location=participant.location,
                created=current_timestamp(),
                event=event,
                deployment_id=event.deployment_id,
                data={})

    # if submission is None, there's no submission
    if submission is None:
        response = {
            'message': gettext('Could not update data. Please check your ID'),
            'status': 'error'
        }
        return jsonify(response), HTTPStatus.BAD_REQUEST

    data = submission.data.copy() if submission.data else {}
    payload2 = payload.copy()
    location_data = payload2.pop('location', None)
    for tag in form.tags:
        field = form.get_field_by_tag(tag)
        if field['type'] == 'multiselect':
            value = payload.get(tag)
            if value is not None:
                try:
                    payload2[tag] = sorted(value)
                except Exception:
                    pass

    attachments = []
    deleted_attachments = []
    for tag, wrapper in request.files.items():
        if tag not in form.tags:
            continue
        original_field_data = submission.data.get(tag)
        identifier = uuid4()

        # process only image uploads
        if wrapper and wrapper.mimetype.startswith('image/'):
            # mark the original image attachment for deletion
            if original_field_data is not None:
                original_attachment = \
                    SubmissionImageAttachment.query.filter_by(
                        uuid=original_field_data).first()
                if original_attachment is not None:
                    deleted_attachments.append(original_attachment)

            if wrapper.filename != '':
                data[tag] = identifier.hex
                attachments.append(
                    SubmissionImageAttachment(
                        photo=wrapper, submission=submission,
                        uuid=identifier
                    )
                )

    db.session.add_all(attachments)
    for attachment in deleted_attachments:
        db.session.delete(attachment)

    if data != payload2:
        data.update(payload2)
        geopoint = 'SRID=4326; POINT({lon:f} {lat:f})'.format(
            lat=location_data[1],
            lon=location_data[0]
        ) if location_data is not None else None
        if submission.id is None:
            submission.data = data
            if geopoint is not None:
                submission.geom = geopoint
            submission.save()
        else:
            query = Submission.query.filter_by(id=submission.id)
            update_params = {'data': data, 'unreachable': False}
            if geopoint is not None:
                update_params['geom'] = geopoint
            query.update(update_params, synchronize_session=False)
            db.session.commit()

        submission.update_related(data)
        if submission.master is not None:
            submission.update_master_offline_status()
        update_submission_version(submission)

    message_text = make_message_text(form, participant, data)
    sender = participant.primary_phone or participant.participant_id
    message = messages.log_message(
        event=submission.event, direction='IN', text=message_text,
        sender=sender, message_type='API')
    message.participant = participant
    message.submission_id = submission.id
    message.save()

    # return the submission ID so that any updates
    # (for example, sending attachments) can be done
    response = {
        'message': gettext('Data successfully submitted'),
        'status': 'ok',
        'submission': submission.id,
    }

    return jsonify(response)
