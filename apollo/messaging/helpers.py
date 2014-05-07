from ..formsframework.forms import build_questionnaire
from .forms import retrieve_form
from .utils import parse_text, parse_responses
from flask.ext.babel import lazy_gettext as _
from werkzeug.datastructures import MultiDict


def parse_message(form):
    message = form.get_message()
    (prefix, participant_id, form_type, responses, comment) = parse_text(
        message['text'])
    if (prefix and participant_id and form_type and responses):
        form_doc = retrieve_form(prefix, form_type)
        if form_doc:
            form_data = MultiDict(
                {'form': form_doc.pk, 'participant': participant_id,
                 'sender': message['sender'], 'comment': comment})
            form_data.update(parse_responses(responses, form_doc.form_type))
            questionnaire = build_questionnaire(form_doc, form_data)

            if questionnaire.validate():
                questionnaire.save()
                return _('Thank you! Your report was received!'
                         ' You sent: {text}') \
                    .format(text=message.get('text', ''))
            else:
                if 'participant' in questionnaire.errors:
                    return _('Observer ID not found. Please resend with valid '
                             'Observer ID. You sent: {text}') \
                        .format(text=message.get('text', ''))
                elif '__all__' in questionnaire.errors:
                    # Save any valid data
                    questionnaire.save()
                    return _('Unknown question codes: "{questions}". '
                             'You sent: {text}') \
                        .format(questions=', '.join(
                                sorted([
                                    q for q in questionnaire.errors['__all__']
                                ])),
                                text=message.get('text', ''))
                else:
                    # Save any valid data
                    questionnaire.save()
                    return _('Invalid response(s) for question(s):'
                             ' "{questions}". You sent: {text}') \
                        .format(
                            questions=', '.join(sorted(
                                questionnaire.errors.keys())),
                            text=message.get('text', ''))
    return _('Invalid message: "{text}". Please check and resend!') \
        .format(text=message.get('text', ''))
