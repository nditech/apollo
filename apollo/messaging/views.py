from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
from messaging.forms import KannelForm, TelerivetForm
from messaging.utils import generate_questionnaire_from_message


def parse_message(form, request):
    message = form.get_message()
    questionnaire = generate_questionnaire_from_message(request, **message)
    if questionnaire.is_valid():
        questionnaire.save()
        return _('Thank you! Your report was received! You sent: {text}') \
            .format(text=message.get('text', ''))
    else:
        if 'participant' in questionnaire.errors:
            return _('Observer ID not found. Please resend with valid '
                     'Observer ID. You sent: {text}') \
                .format(text=message.get('text', ''))
        elif 'values' in questionnaire.errors:
            return _('Invalid response(s) for question(s): "{questions}". '
                     'You sent: {text}') \
                .format(questions=questionnaire.errors['values'],
                        text=message.get('text', ''))
        elif 'questions' in questionnaire.errors:
            return _('Unknown question codes: "{questions}". '
                     'You sent: {text}') \
                .format(questions=questionnaire.errors['questions'],
                        text=message.get('text', ''))
    return _('Invalid message: "{text}". Please check and resend!') \
        .format(text=message.get('text', ''))


def kannel_view(request):
    form = KannelForm(request.GET)
    if form.is_valid():
        response = parse_message(form, request)
        return HttpResponse(response)
    return HttpResponse('')


def telerivet_view(request):
    form = TelerivetForm(request.POST)
    if form.is_valid():
        response = parse_message(form, request)
        return HttpResponse(response)
    return HttpResponse('')
