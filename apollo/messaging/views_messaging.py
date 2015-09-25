from apollo.frontend import route
from apollo import services
from apollo.core import csrf
from apollo.messaging.forms import KannelForm, TelerivetForm
from apollo.messaging.helpers import parse_message
from apollo.messaging.utils import parse_text
from flask import Blueprint, make_response, request, g, current_app
import json


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

    form = TelerivetForm(request.form)
    if form.validate():
        msg = form.get_message()
        incoming = services.messages.log_message(
            event=g.event, sender=msg.get('sender'), text=msg.get('text'),
            direction='IN', timestamp=msg.get('timestamp'))

        response_text, submission, had_errors = parse_message(form)
        response = {'messages': [{'content': response_text}]}
        http_response = make_response(json.dumps(response))
        http_response.headers['Content-Type'] = 'application/json'

        outgoing = services.messages.log_message(
            event=g.event, recipient=msg.get('sender'), text=response_text,
            direction='OUT', timestamp=msg.get('timestamp'))

        update_datastore(incoming, outgoing, submission, had_errors)

        return http_response
    return ""
