# -*- coding: utf-8 -*-
from flask import g
from flask_babelex import gettext
from werkzeug.datastructures import MultiDict

from apollo import services
from apollo.core import force_locale
from apollo.formsframework.forms import build_questionnaire
from apollo.messaging.forms import retrieve_form
from apollo.messaging.utils import (
    get_unsent_codes,
    parse_text,
    parse_responses,
)
from apollo.participants import models


def _get_response_locale(message: str, sender: str, submission, event) -> str:
    if submission and submission.participant:
        locale = submission.participant.locale or ""
    else:
        participant = lookup_participant(message, sender, event)
        if participant and participant.locale:
            locale = participant.locale
        else:
            locale = ""
    
    return locale


def parse_message(form):
    message = form.get_message()
    submission = None
    had_errors = False
    response_dict = None

    (
        prefix,
        participant_id,
        exclamation,
        form_serial,
        responses,
        comment,
    ) = parse_text(message["text"])
    event = g.event
    locale = _get_response_locale(
        message["text"], message["sender"], submission, event)
    if prefix and participant_id and responses:
        form_doc = retrieve_form(prefix, exclamation)
        if form_doc:
            response_dict, extra = parse_responses(responses, form_doc)
        if form_doc and response_dict:
            form_data = MultiDict(
                {
                    "form": form_doc.id,
                    "participant": participant_id,
                    "sender": message["sender"],
                    "form_serial": form_serial,
                    "comment": comment,
                }
            )
            form_data.update(response_dict)
            questionnaire = build_questionnaire(form_doc, form_data)

            if questionnaire.validate():
                submission = questionnaire.save()
                event = submission.event if submission else event
                locale = _get_response_locale(
                    message["text"], message["sender"], submission, event)

                with force_locale(locale):
                    # if submission returns empty, then the participant
                    # was not meant to send this text.
                    if submission is None:
                        reply = gettext(
                            "Invalid message: %(text)s. Please check and resend!",
                            text=message.get("text", ""),
                        )
                        return reply, submission, True

                    # switch to the participant's locale if valid,
                    # or use the default
                    # check if there were extra fields sent in
                    diff = set(response_dict.keys()).difference(
                        set(questionnaire.data.keys())
                    )
                    if not diff and not extra:
                        # check that the data sent was not partial
                        unused_tags = get_unsent_codes(
                            form_doc, response_dict.keys()
                        )
                        if (
                            unused_tags
                            and getattr(g, "deployment", False)
                            and getattr(
                                g.deployment,
                                "enable_partial_response_for_messages",
                                False,
                            )
                        ):
                            reply = gettext(
                                "Thank you, but your message may be missing "
                                "%(unused_codes)s. You sent: %(text)s",
                                unused_codes=", ".join(unused_tags),
                                text=message.get("text", ""),
                            )

                            return reply, submission, had_errors
                        return (
                            gettext(
                                "Thank you! Your report was received!"
                                " You sent: %(text)s",
                                text=message.get("text", ""),
                            ),
                            submission,
                            had_errors,
                        )
                    elif diff:
                        # TODO: replace .format() calls
                        had_errors = True
                        return (
                            gettext(
                                'Unknown question codes: "%(questions)s". '
                                "You sent: %(text)s",
                                questions=", ".join(sorted(diff)),
                                text=message.get("text", ""),
                            ),
                            submission,
                            had_errors,
                        )
                    elif extra:
                        had_errors = True
                        return (
                            gettext(
                                'Invalid text sent: "%(extra)s". '
                                "You sent: %(text)s",
                                extra=extra,
                                text=message.get("text", ""),
                            ),
                            submission,
                            had_errors,
                        )
            else:
                had_errors = True
                event = submission.event if submission else event
                locale = _get_response_locale(
                    message["text"], message["sender"], submission, event)
                with force_locale(locale):
                    if "participant" in questionnaire.errors:
                        return (
                            gettext(
                                "Observer ID not found. Please resend with valid "
                                "Observer ID. You sent: %(text)s",
                                text=message.get("text", ""),
                            ),
                            submission,
                            had_errors,
                        )
                    else:
                        # Save any valid data
                        submission = questionnaire.save()
                        return (
                            gettext(
                                "Invalid response(s) for question(s):"
                                ' "%(questions)s". You sent: %(text)s',
                                questions=", ".join(
                                    sorted(questionnaire.errors.keys())
                                ),
                                text=message.get("text", ""),
                            ),
                            submission,
                            had_errors,
                        )

    had_errors = True
    with force_locale(locale):
        return (
            gettext(
                "Invalid message: %(text)s. Please check and resend!",
                text=message.get("text", ""),
            ),
            submission,
            had_errors,
        )


def lookup_participant(message: str, sender: str, event=None):
    '''
    Looks up a participant given a message text, a sender number and an event
    Arguments:
        - message: a message string
        - sender: a message sender (a phone number, likely in E.164 format)
        - event: an event instance. if it's None, no participant will be
                 returned

    Returns a participant or None
    '''
    participant = None
    unused, participant_id, unused, unused, unused, unused = parse_text(
        message)

    participant_set_id = event.participant_set_id if event else None

    if participant_id:
        participant = services.participants.find(
            participant_set_id=participant_set_id,
            participant_id=participant_id
        ).first()

    if not participant:
        clean_number = sender.replace('+', '')
        participant = services.participants.query.join(
            models.PhoneContact,
            models.Participant.id == models.PhoneContact.participant_id
        ).filter(
            models.Participant.participant_set_id == participant_set_id,
            models.PhoneContact.number == clean_number
        ).first()

    return participant
