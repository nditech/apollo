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
    3. Exclamation: The exclamation is used as a guide in searching for the form
    to process the responses. It will contain the value of True or False.
    Exlamation isn't used in all cases in finding the form to
    process the responses it is only used when the value is explicitly
    True.
    4. Responses: This represents the responses contained in the text that are
    returned. The responses are only returned as plain text and will need to
    be parsed by the :function:`parse_responses` method to extract individual
    responses.
    5. Comment: The comments sent by the participant are returned in this
    position.

    The method returns these values in the following order:
    (prefix, participant_id, exclamation, responses, comments)
    '''
    from flask import current_app
    config = current_app.config

    prefix = participant_id = exclamation = responses = comment = None
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
        exclamation = True if match.group('exclamation') else False
        responses = match.group('responses') or None
    comment = text[at_position + 1:].strip() if at_position != -1 else None

    return (prefix, participant_id, exclamation, responses, comment)


def parse_responses(responses_text, form):
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
    fields = [fi for group in form.groups for fi in group.fields
              if not fi.is_comment_field]
    numeric_fields = [f.name for f in fields if not f.represents_boolean]
    boolean_fields = [f.name for f in fields if f.represents_boolean]

    substrate = responses_text
    responses = OrderedDict()
    # process numeric fields first
    pattern = re.compile(r'(?P<tag>{})(?P<answer>\d+)'.format(
        '|'.join(numeric_fields)), flags=re.I)
    responses.update(
        ((r.group('tag').upper(), r.group('answer')) for r in
            pattern.finditer(responses_text)))

    # remove the found data
    substrate = pattern.sub('', responses_text)

    # fix for bug where boolean_fields is an empty iterable
    if not boolean_fields:
        return responses

    # next, process boolean fields
    pattern2 = re.compile(r'(?P<tag>{})'.format('|'.join(boolean_fields)),
                          flags=re.I)
    responses.update(
        ((r.group('tag').upper(), 1) for r in pattern2.finditer(substrate)))

    return responses
