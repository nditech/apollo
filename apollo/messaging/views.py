from core.utils.forms import build_questionnaire, retrieve_form
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
from messaging.forms import KannelForm, TelerivetForm
from messaging.utils import parse_text, parse_responses


def parse_message(form, deployment):
    message = form.get_message()
    (prefix, participant_id, form_type, responses, comment) = parse_text(
        message['text'])
    if (prefix and participant_id and form_type and responses):
        form_doc = retrieve_form(deployment, prefix, form_type)
        if form_doc:
            questionnaire_form = build_questionnaire(form_doc)
            form_data = {'prefix': prefix, 'participant': participant_id,
                         'sender': message['sender'], 'comment': comment}
            form_data.update(parse_responses(responses))
            questionnaire = questionnaire_form(form_data)

            if questionnaire.is_valid():
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
                                [q for q in questionnaire.errors['__all__']]),
                                text=message.get('text', ''))
                else:
                    # Save any valid data
                    questionnaire.save()
                    return _('Invalid response(s) for question(s):'
                             ' "{questions}". You sent: {text}') \
                        .format(
                            questions=', '.join(questionnaire.errors.keys()),
                            text=message.get('text', ''))
    return _('Invalid message: "{text}". Please check and resend!') \
        .format(text=message.get('text', ''))


def kannel_view(request):
    form = KannelForm(request.GET)
    if form.is_valid():
        response = parse_message(form, getattr(request, 'deployment', None))
        return HttpResponse(response)
    return HttpResponse('')


def telerivet_view(request):
    form = TelerivetForm(request.POST)
    if form.is_valid():
        response = parse_message(form, getattr(request, 'deployment', None))
        return HttpResponse(response)
    return HttpResponse('')
