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


def parse_text(text):
    '''
    This method accepts the contents of a text message and parses out the
    following pieces of information:

    1. Prefix: This is the prefix that will be used in searching for the
    form to process the responses in the text.
    2. Participant_id: The participant_id is used to identify the participant
    contributing this submission.
    3. Form_type: The form_type is used as a guide in searching for the form
    to process the responses. It will contain the value of None, 'CHECKLIST' or
    'INCIDENT'. Form_type isn't used in all cases in finding the form to
    process the responses it is only used when the value is explicitly
    'INCIDENT'.
    4. Responses: This represents the responses contained in the text that are
    returned. The responses are only returned as plain text and will need to
    be parsed by the :function:`parse_responses` method to extract individual
    responses.
    5. Comment: The comments sent by the participant are returned in this
    position.

    The method returns these values in the following order:
    (prefix, participant_id, form_type, responses, comments)
    '''
    prefix = participant_id = form_type = responses = comment = None
    text = unicode(text)
    # regular expression for a valid text message
    pattern = re.compile(
        r'^(?P<prefix>[A-Z]+)(?P<participant_id>\d+)(?P<exclamation>!?)'
        '(?P<responses>[A-Z0-9]*)$', re.I)

    at_position = text.find("@")

    # remove unwanted punctuation characters and convert known characters
    # like i, l to 1 and o to 0. This will not be applied to the comment
    # section.
    text = filter(lambda s: s not in PUNCTUATIONS, text[:at_position]) \
        .translate(TRANS_TABLE) + text[at_position:] \
        if at_position != -1 \
        else filter(lambda s: s not in PUNCTUATIONS, text) \
        .translate(TRANS_TABLE)
    match = pattern.match(text[:at_position] if at_position != -1 else text)

    # if there's a match, then extract the required features
    if match:
        prefix = match.group('prefix') or None
        participant_id = match.group('participant_id') or None
        form_type = 'INCIDENT' if match.group('exclamation') else 'CHECKLIST'
        responses = match.group('responses') or None
    comment = text[at_position + 1:] if at_position != -1 else None

    return (prefix, participant_id, form_type, responses, comment)


def parse_responses(responses_text, form_type='CHECKLIST'):
    '''
    The :function:`parse_responses` method accepts the _responses_ section of
    an incoming text message and generates a dictionary of key value pairs of
    response questions and answers.

    :param:`responses_text` - The responses portion of the text message
    (e.g. AA1BA2)
    :param:`form_type` - (Optional) the form type guiding the parsing of the
    responses. Responses for Incident Forms (e.g. ABCDE) are different in
    nature from that of Checklist Forms (e.g. AA1BA2CC10).
    '''
    if form_type == 'INCIDENT':
        # one alphabet represents a critical incident
        p = re.compile(r'(?P<question>[A-Z])')
        responses = dict(
            [(r.group('question'), 1) for r in p.finditer(responses_text)])
    else:
        # responses for checklist questions are in the form AA111
        # where AA is the alphabetic question code and 111 is the response.
        # This may occur more than once in the response text.
        p = re.compile(r'(?P<question>[A-Z]+)(?P<answer>\d*)')
        responses = dict(
            [(r.group('question'), r.group('answer'))
             for r in p.finditer(responses_text)])
    return responses


def generate_questionnaire_from_message(request, sender, text):
    '''
    Generates a bound form for validating and saving form data to the database.

    :param:`request` - The context for the request being processed. Useful for
    providing access to the deployment to use.
    :param:`sender` - The phone number of the sender of the text message
    :param:`text` - The contents of the text message sent.
    '''
    form_fields = {}
    (prefix, participant_id, form_type, responses, comment) = parse_text(text)
    events_in_deployment = Event.objects.filter(
        deployment=getattr(request, 'deployment'))

    # find the first form that matches the prefix and optionally form type
    # for the events in the deployment.
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

    form_data = {'prefix': prefix, 'participant': participant_id,
                 'sender': sender, 'comment': comment}
    form_data.update(parse_responses(responses))

    # create a custom form based on the generated attributes
    # (groups and fields) of the form and bind it with data extracted from
    # the text message.
    return type('QuesationnaireForm', (BaseQuestionnaireForm,),
                form_fields)(form_data)
