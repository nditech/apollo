from collections import OrderedDict
import re


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
    from flask import current_app
    config = current_app.config

    prefix = participant_id = form_type = responses = comment = None
    text = unicode(text)
    # regular expression for a valid text message
    pattern = re.compile(
        r'^(?P<prefix>[A-Z]+)(?P<participant_id>\d+)'
        '(?P<exclamation>!?)(?P<responses>[A-Z0-9]*)$', re.I)

    at_position = text.find("@")

    # remove unwanted punctuation characters and convert known characters
    # like i, l to 1 and o to 0. This will not be applied to the comment
    # section.
    text = filter(lambda s: s not in config.get('PUNCTUATIONS'),
                  text[:at_position]) \
        .translate(config.get('TRANS_TABLE')) + text[at_position:] \
        if at_position != -1 \
        else filter(lambda s: s not in config.get('PUNCTUATIONS'), text) \
        .translate(config.get('TRANS_TABLE'))

    at_position = text.find("@")
    match = pattern.match(text[:at_position] if at_position != -1 else text)

    # if there's a match, then extract the required features
    if match:
        prefix = match.group('prefix') or None
        participant_id = match.group('participant_id') or None
        form_type = 'INCIDENT' if match.group('exclamation') else 'CHECKLIST'
        responses = match.group('responses') or None
    comment = text[at_position + 1:].strip() if at_position != -1 else None

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
        p = re.compile(r'(?P<question>[A-Z])', re.I)
        responses = dict(
            [(r.group('question').upper(), 1)
             for r in p.finditer(responses_text)])
    else:
        # responses for checklist questions are in the form AA111
        # where AA is the alphabetic question code and 111 is the response.
        # This may occur more than once in the response text.
        p = re.compile(r'(?P<question>[A-Z]+)(?P<answer>\d*)', re.I)
        responses = dict(
            [(r.group('question').upper(), r.group('answer'))
             for r in p.finditer(responses_text)])
    return responses


def parse_responses_ex(responses_text, form):
    '''
    The :function:`parse_responses_ex` function accepts the _responses_
    section of an incoming text message and generates a(n ordered) dictionary
    of key value pairs response questions and answers.

    :param:`responses_text` - The responses portion of the text message
    (e.g. AA1BA2)
    :param:`form` - A `Form` instance to match the responses against.
    The way the matching is done is dependent on the `FormField` instances
    defined in `form`: numeric fields are first matched, then boolean
    fields are.
    '''
    fields = [fi for group in form.groups for fi in group.fields]
    numeric_fields = [f.name for f in fields if not f.represents_boolean]
    boolean_fields = [f.name for f in fields if f.represents_boolean]

    substrate = responses_text
    responses = OrderedDict()
    for f in numeric_fields:
        pattern = '{}(?P<answer>\d*)'.format(f)
        result = re.match(pattern, substrate, re.I)
        if result:
            responses[f] = result.group('answer')
            substrate = re.sub(pattern, '', substrate)

    for f in boolean_fields:
        if re.match(f, substrate, re.I):
            responses[f] = 1
            substrate = re.sub(f, '', substrate)

    return responses
