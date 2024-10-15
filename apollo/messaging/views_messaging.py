# -*- coding: utf-8 -*-
import json
import re

from flask import Blueprint, current_app, g, make_response, request
from unidecode import unidecode

from apollo import services

from ..core import csrf, db
from ..frontend import route
from ..frontend.helpers import get_event
from ..messaging.forms import KannelForm, TelerivetForm
from ..messaging.helpers import lookup_participant, parse_message

bp = Blueprint("messaging", __name__)


def update_datastore(inbound, outbound, submission, had_errors):
    """Utility method to update inbound and outbound message objects."""
    outbound.originating_message_id = inbound.id
    models_to_save = [outbound]

    if submission:
        participant = submission.participant
    else:
        event = g.event
        participant = lookup_participant(inbound.text, inbound.sender, event)

    if participant:
        inbound.submission = submission
        inbound.participant = participant

        outbound.participant = participant
        outbound.submission = submission

        if not had_errors:
            participant.accurate_message_count += 1

        participant.message_count += 1
        models_to_save.append(participant)
        models_to_save.append(inbound)

    db.session.add_all(models_to_save)
    db.session.commit()


@route(bp, "/messaging/kannel", methods=["GET"])
def kannel_view():
    """View for handling inbound messages from Kannel."""
    secret = request.args.get("secret")

    # only allow requests that contain the gateway secret
    if secret != current_app.config.get("MESSAGING_SECRET"):
        return ""

    form = KannelForm(request.args)
    if form.validate():
        msg = form.get_message()

        response, submission, had_errors = parse_message(form)
        event = submission.event if submission else get_event()

        incoming = services.messages.log_message(
            event=event, sender=msg.get("sender"), text=msg.get("text"), direction="IN", timestamp=msg.get("timestamp")
        )
        outgoing = services.messages.log_message(
            event=event, recipient=msg.get("sender"), text=response, direction="OUT"
        )

        update_datastore(incoming, outgoing, submission, had_errors)

        if current_app.config.get("TRANSLITERATE_OUTPUT"):
            response = unidecode(response)

        return response
    return ""


@csrf.exempt
@route(bp, "/messaging/telerivet", methods=["POST"])
def telerivet_view():
    """View for handling inbound messages from Telerivet."""
    secret = request.form.get("secret")

    if secret != current_app.config.get("MESSAGING_SECRET"):
        return ""

    # if the sender is the same as the recipient, then don't respond
    if re.sub(r"[^\d]", "", request.form.get("from_number")) == re.sub(r"[^\d]", "", request.form.get("to_number")):
        return ""

    form = TelerivetForm(request.form)
    if form.validate():
        msg = form.get_message()

        response_text, submission, had_errors = parse_message(form)
        event = submission.event if submission else get_event()

        incoming = services.messages.log_message(
            event=event, sender=msg.get("sender"), text=msg.get("text"), direction="IN", timestamp=msg.get("timestamp")
        )
        outgoing = services.messages.log_message(
            event=event,
            recipient=msg.get("sender"),
            text=response_text,
            direction="OUT",
            timestamp=msg.get("timestamp"),
        )

        update_datastore(incoming, outgoing, submission, had_errors)

        if current_app.config.get("TRANSLITERATE_OUTPUT"):
            response_text = unidecode(response_text)
        response = {"messages": [{"content": response_text}]}
        http_response = make_response(json.dumps(response, ensure_ascii=False))
        http_response.headers["Content-Type"] = "application/json; charset=utf-8"

        return http_response
    return ""
