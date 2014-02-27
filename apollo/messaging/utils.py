from core.documents import Event, Form
from messaging.forms import BaseQuestionnaireForm
from django import forms
from django.conf import settings
import re
import string

PUNCTUATIONS = filter(lambda s: s not in settings.ALLOWED_PUNCTUATIONS,
                      string.punctuation) + ' '
TRANS_TABLE = dict((ord(char_from), ord(char_to))
                   for char_from, char_to in settings.CHARACTER_TRANSLATIONS)


# returns: (prefix, participant_id, form_type, responses, comments)
def parse_text(text):
    prefix = participant_id = form_type = responses = comments = None
    text = unicode(text)
    pattern = re.compile(
        r'^(?P<prefix>[A-Z]+)(?P<participant_id>\d+)(?P<exclamation>!?)'
        '(?P<responses>[A-Z0-9]*)$', re.I)

    at_position = text.find("@")
    text = filter(lambda s: s not in PUNCTUATIONS, text[:at_position]) \
        .translate(TRANS_TABLE) + text[at_position:] \
        if at_position != -1 \
        else filter(lambda s: s not in PUNCTUATIONS, text) \
        .translate(TRANS_TABLE)
    match = pattern.match(text[:at_position] if at_position != -1 else text)

    if match:
        prefix = match.group('prefix') or None
        participant_id = match.group('participant_id') or None
        form_type = 'INCIDENT' if match.group('exclamation') else 'CHECKLIST'
        responses = match.group('responses') or None
    comments = text[at_position + 1:] if at_position != -1 else None

    return (prefix, participant_id, form_type, responses, comments)


def parse_responses(responses_text, form_type='CHECKLIST'):
    if form_type == 'INCIDENT':
        p = re.compile(r'(?P<question>[A-Z])')
        responses = dict(
            [(r.group('question'), 1) for r in p.finditer(responses_text)])
    else:
        p = re.compile(r'(?P<question>[A-Z]+)(?P<answer>\d*)')
        responses = dict(
            [(r.group('question'), r.group('answer'))
             for r in p.finditer(responses_text)])
    return responses


def generate_questionnaire_from_message(request, sender, text):
    form_fields = {}
    (prefix, participant_id, form_type, responses, comments) = parse_text(text)
    events_in_deployment = Event.objects.filter(
        deployment=getattr(request, 'deployment'))
    if form_type == 'INCIDENT':
        form = Form.objects.filter(
            events__in=events_in_deployment, prefix__iexact=prefix,
            form_type=form_type).first()
    else:
        form = Form.objects.filter(
            events__in=events_in_deployment, prefix__iexact=prefix).first()
    if form:
        form_groups = []
        for group in form.groups:
            form_group = (group.name, {'fields': [], 'legend': group.name})
            for field in group.fields:
                if field.options:
                    if field.allows_multiple_values:
                        form_fields[field.name] = forms.MultipleChoiceField(
                            choices=field.options.items(), required=False,
                            help_text=field.description, label=field.name)
                    else:
                        form_fields[field.name] = forms.ChoiceField(
                            choices=field.options.items(), required=False,
                            help_text=field.description, label=field.name)
                else:
                    if form.form_type == u'CHECKLIST':
                        form_fields[field.name] = forms.IntegerField(
                            max_value=field.max_value or 9999,
                            min_value=field.min_value or 0, required=False,
                            help_text=field.description, label=field.name)
                    else:
                        form_fields[field.name] = forms.BooleanField(
                            required=False, help_text=field.description,
                            label=field.name, widget=forms.CheckboxInput())

                form_group[1]['fields'].append(field.name)
            form_groups.append(form_group)

    metaclass = type('Meta', (), {'fieldsets': form_groups})
    form_fields['Meta'] = metaclass
    # FIXME: This method should return an instantiated form with
    # parsed input
    return type('QuesationnaireForm', (BaseQuestionnaireForm,), form_fields)
