from . import route
from .. import services
from ..messaging.forms import KannelForm, TelerivetForm
from ..messaging.helpers import parse_message
from ..messaging.utils import parse_text
from flask import Blueprint, make_response, request, g
import json


bp = Blueprint('messaging', __name__)


def lookup_participant(msg):
    participant = None
    unused, participant_id, unused, unused, unused = parse_text(msg.text)

    if participant_id:
        participant = services.participants.get(participant_id=participant_id)

    if not participant:
        try:
            clean_number = msg.sender.replace('+', '')
            participant = services.participants.get(
                phones__number__contains=clean_number
            )
        except services.participants.__model__.MultipleObjectsReturned:
            participant = None

    return participant


@route(bp, '/messaging/kannel', methods=['GET'])
def kannel_view():
    form = KannelForm(request.args)
    if form.validate():
        msg = form.get_message()
        incoming = services.messages.log_message(
            event=g.event, sender=msg.get('sender'), text=msg.get('text'),
            direction='IN')

        response, submission = parse_message(form)

        outgoing = services.messages.log_message(
            event=g.event, recipient=msg.get('sender'), text=response,
            direction='OUT')

        if submission:
            incoming.update(
                set__participant=submission.contributor,
                set__submission=submission)
            outgoing.update(set__participant=submission.contributor)

        return response
    return ""


@route(bp, '/messaging/telerivet', methods=['POST'])
def telerivet_view():
    form = TelerivetForm(request.form)
    if form.validate():
        msg = form.get_message()
        incoming = services.messages.log_message(
            event=g.event, sender=msg.get('sender'), text=msg.get('text'),
            direction='IN')

        response_text, submission = parse_message(form)
        response = {'messages': [{'content': response_text}]}
        http_response = make_response(json.dumps(response))
        http_response.headers['Content-Type'] = 'application/json'

        outgoing = services.messages.log_message(
            event=g.event, recipient=msg.get('sender'), text=response_text,
            direction='OUT')

        if submission:
            incoming.update(
                set__participant=submission.contributor,
                set__submission=submission)
            outgoing.update(set__participant=submission.contributor)

        return http_response
    return ""
