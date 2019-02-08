# -*- coding: utf-8 -*-
from apollo.frontend import route
from apollo import services
from apollo.core import csrf
from apollo.messaging.forms import KannelForm, TelerivetForm
from apollo.messaging.helpers import parse_message
from apollo.messaging.utils import parse_text
from apollo.submissions.tasks import update_submission
from flask import Blueprint, make_response, request, g, current_app
import json
import re
from unidecode import unidecode


bp = Blueprint('messaging', __name__)


def lookup_participant(msg, event=None):
    participant = None
    unused, participant_id, unused, unused, unused = parse_text(msg.text)

    evt = getattr(g, 'event', None) or event

    if participant_id:
        participant = services.participants.get(
            event=evt,
            participant_id=participant_id
        )

    if not participant:
        try:
            clean_number = msg.sender.replace('+', '')
            participant = services.participants.get(
                event=evt,
                phones__number__contains=clean_number
            )
        except services.participants.__model__.MultipleObjectsReturned:
            participant = None

    return participant


def update_datastore(inbound, outbound, submission, had_errors):
    if submission:
        update_submission.delay(str(submission.pk))
        participant = submission.contributor
    else:
        participant = lookup_participant(inbound)

    if participant:
        inbound.update(
            set__participant=participant,
            set__submission=submission
        )
        outbound.update(
            set__participant=participant,
            set__submission=submission
        )

        if not had_errors:
            participant.update(inc__accurate_message_count=1)

        participant.update(inc__message_count=1)


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

        if current_app.config.get(u'TRANSLITERATE_OUTPUT'):
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
        if current_app.config.get(u'TRANSLITERATE_OUTPUT'):
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
