# -*- coding: utf-8 -*-
import json
import re

from flask import Blueprint, make_response, request, g, current_app
from unidecode import unidecode

from apollo import models, services
from apollo.core import csrf
from apollo.frontend import route
from apollo.messaging.forms import KannelForm, TelerivetForm
from apollo.messaging.helpers import parse_message
from apollo.messaging.utils import parse_text


bp = Blueprint('messaging', __name__)


def lookup_participant(msg, event=None):
    participant = None
    unused, participant_id, unused, unused, unused = parse_text(msg.text)

    evt = getattr(g, 'event', None) or event

    if participant_id:
        participant = services.participants.find(
            participant_set_id=evt.participant_set_id,
            participant_id=participant_id
        ).first()

    if not participant:
        clean_number = msg.sender.replace('+', '')
        participant = services.participants.query.join(
            models.ParticipantPhone,
            models.Participant.id == models.ParticipantPhone.participant_id
        ).join(
            models.Phone,
            models.ParticipantPhone.phone_id == models.Phone.id
        ).filter(
            models.Participant.participant_set_id == evt.participant_set_id,
            models.Phone.number == clean_number
        ).first()

    return participant


def update_datastore(inbound, outbound, submission, had_errors):
    if submission:
        participant = submission.participant
    else:
        participant = lookup_participant(inbound)

    if participant:
        inbound.submission = submission
        inbound.participant = participant

        outbound.participant = participant
        outbound.submission = submission

        if not had_errors:
            participant.accurate_message_count += 1

        participant.message_count += 1
        participant.save()


@route(bp, '/messaging/kannel', methods=['GET'])
def kannel_view():
    secret = request.args.get('secret')

    # only allow requests that contain the gateway secret
    if secret != current_app.config.get('MESSAGING_SECRET'):
        return ''

    form = KannelForm(request.args)
    if form.validate():
        msg = form.get_message()
        incoming = services.messages.log_message(
            event=g.event, sender=msg.get('sender'), text=msg.get('text'),
            direction='IN', timestamp=msg.get('timestamp'))

        response, submission, had_errors = parse_message(form)

        if current_app.config.get('TRANSLITERATE_OUTPUT'):
            response = unidecode(response)

        outgoing = services.messages.log_message(
            event=g.event, recipient=msg.get('sender'), text=response,
            direction='OUT', timestamp=msg.get('timestamp'))

        update_datastore(incoming, outgoing, submission, had_errors)

        return response
    return ""


@csrf.exempt
@route(bp, '/messaging/telerivet', methods=['POST'])
def telerivet_view():
    secret = request.form.get('secret')

    if secret != current_app.config.get('MESSAGING_SECRET'):
        return ''

    # if the sender is the same as the recipient, then don't respond
    if re.sub(r'[^\d]', '', request.form.get('from_number')) == re.sub(r'[^\d]', '', request.form.get('to_number')):
        return ''

    form = TelerivetForm(request.form)
    if form.validate():
        msg = form.get_message()
        incoming = services.messages.log_message(
            event=g.event, sender=msg.get('sender'), text=msg.get('text'),
            direction='IN', timestamp=msg.get('timestamp'))

        response_text, submission, had_errors = parse_message(form)
        if current_app.config.get('TRANSLITERATE_OUTPUT'):
            response_text = unidecode(response_text)
        response = {'messages': [{'content': response_text}]}
        http_response = make_response(json.dumps(response))
        http_response.headers['Content-Type'] = 'application/json'

        outgoing = services.messages.log_message(
            event=g.event, recipient=msg.get('sender'), text=response_text,
            direction='OUT', timestamp=msg.get('timestamp'))

        update_datastore(incoming, outgoing, submission, had_errors)

        return http_response
    return ""
