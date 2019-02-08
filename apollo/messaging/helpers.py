# -*- coding: utf-8 -*-
from apollo.formsframework.forms import build_questionnaire
from apollo.messaging.forms import retrieve_form
from apollo.messaging.utils import parse_text, parse_responses
from flask.ext.babel import lazy_gettext as _
from werkzeug.datastructures import MultiDict


def parse_message(form):
    message = form.get_message()
    submission = None
    had_errors = False
    response_dict = None

    (prefix, participant_id, exclamation, responses, comment) = parse_text(
        message['text'])
    if (prefix and participant_id and responses):
        form_doc = retrieve_form(prefix, exclamation)
        if form_doc:
            response_dict, extra = parse_responses(responses, form_doc)
        if form_doc and response_dict:
            form_data = MultiDict(
                {'form': form_doc.pk, 'participant': participant_id,
                 'sender': message['sender'], 'comment': comment})
            form_data.update(response_dict)
            questionnaire = build_questionnaire(form_doc, form_data)

            if questionnaire.validate():
                submission = questionnaire.save()

                # if submission returns empty, then the participant
                # was not meant to send this text.
                # TODO: add response for no recorded submission

                # check if there were extra fields sent in
                diff = set(response_dict.keys()).difference(
                    set(questionnaire.data.keys()))
                if not diff and not extra:
                    return (
                        _('Thank you! Your report was received!'
                          ' You sent: {text}')
                        .format(text=message.get('text', '')),
                        submission,
                        had_errors
                    )
                elif diff:
                    had_errors = True
                    return (
                        _('Unknown question codes: "{questions}". '
                          'You sent: {text}')
                        .format(questions=', '.join(sorted(diff)),
                                text=message.get('text', '')),
                        submission,
                        had_errors
                    )
                elif extra:
                    had_errors = True
                    return (_('Invalid text sent: "{extra}". '
                        'You sent: {text}').format(
                            extra=extra, text=message.get('text', '')),
                        submission,
                        had_errors)
            else:
                had_errors = True
                if 'participant' in questionnaire.errors:
                    return (
                        _('Observer ID not found. Please resend with valid '
                          'Observer ID. You sent: {text}')
                        .format(text=message.get('text', '')),
                        submission,
                        had_errors
                    )
                else:
                    # Save any valid data
                    submission = questionnaire.save()
                    return (
                        _('Invalid response(s) for question(s):'
                          ' "{questions}". You sent: {text}')
                        .format(
                            questions=', '.join(sorted(
                                questionnaire.errors.keys())),
                            text=message.get('text', '')),
                        submission,
                        had_errors
                    )
    had_errors = True
    return (
        _('Invalid message: "{text}". Please check and resend!').format(
            text=message.get('text', '')),
        submission,
        had_errors
    )
