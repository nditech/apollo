# -*- coding: utf-8 -*-
from collections import OrderedDict
import re

from unidecode import unidecode


def parse_text(text):
    '''
    This method accepts the contents of a text message and parses out the
    following pieces of information:

    1. Prefix: This is the prefix that will be used in searching for the
    form to process the responses in the text.
    2. Participant_id: The participant_id is used to identify the participant
    contributing this submission.
    3. Exclamation: The exclamation is used as a guide in searching for the
    form to process the responses. It will contain the value of True or False.
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

    prefix = participant_id = exclamation = form_serial = responses = comment = None  # noqa
    text = str(text)
    # regular expression for a valid text message
    pattern = re.compile(
        r'^(?P<prefix>[A-Z]+)(?P<participant_id>\d+)'
        '(?P<exclamation>!?)(?:X(?P<form_serial>\d+))?(?P<responses>[A-Z0-9\s]*)$',  # noqa
        re.I | re.M)

    at_position = text.find("@")

    if config.get('TRANSLITERATE_INPUT'):
        if at_position != -1:
            text = unidecode(text[:at_position]) + text[at_position:]
        else:
            text = unidecode(text)
        at_position = text.find('@')

    # remove unwanted punctuation characters and convert known characters
    # like i, l to 1 and o to 0. This will not be applied to the comment
    # section.
    if at_position != -1:
        data_section = text[:at_position]
        comment_section = text[at_position:]
    else:
        data_section = text
        comment_section = ''

    data_section_stripped = ''.join(
        s for s in data_section if s not in config.get('PUNCTUATIONS'))

    if config.get('TRANSLATE_CHARS'):
        data_section_translated = data_section_stripped.translate(
            config.get('TRANS_TABLE'))
    else:
        data_section_translated = data_section_stripped

    # reconstruct message with translated characters
    # and punctuation filtered out
    text = data_section_translated + comment_section

    at_position = text.find("@")
    match = pattern.match(text[:at_position] if at_position != -1 else text)

    # if there's a match, then extract the required features
    if match:
        prefix = match.group('prefix') or None
        participant_id = match.group('participant_id') or None
        exclamation = True if match.group('exclamation') else False
        form_serial = match.group('form_serial') or None
        responses = match.group('responses') or None
    comment = text[at_position + 1:].strip() if at_position != -1 else None

    return (
        prefix, participant_id, exclamation, form_serial, responses, comment)


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
    fields = [fi for group in form.data['groups'] for fi in group['fields']
              if fi['type'] != 'comment']
    numeric_fields = [f['tag'] for f in fields if f['type'] != 'boolean']
    boolean_fields = [f['tag'] for f in fields if f['type'] == 'boolean']

    substrate = re.sub(r'(\n|\r|\r\n)', '', responses_text)
    responses = OrderedDict()
    # process numeric fields first
    pattern = re.compile(r'(?P<tag>{})(?P<answer>\d+)'.format(
        '|'.join(numeric_fields)), flags=re.I)
    responses.update(
        ((r.group('tag').upper(), r.group('answer')) for r in
            pattern.finditer(substrate)))

    # remove the found data
    substrate = pattern.sub('', substrate)

    # fix for bug where boolean_fields is an empty iterable
    if not boolean_fields:
        return responses, substrate.strip()

    # next, process boolean fields
    pattern2 = re.compile(r'(?P<tag>{})'.format('|'.join(boolean_fields)),
                          flags=re.I)
    responses.update(
        ((r.group('tag').upper(), 1) for r in pattern2.finditer(substrate)))

    # remove the found data
    substrate = pattern2.sub('', substrate)

    # finally, get any unknown tags
    default_pattern = re.compile(r'(?P<tag>[A-Z]+)(?P<answer>\d+)', flags=re.I)
    responses.update(
        (r.group('tag').upper(), r.group('answer')) for r in
        default_pattern.finditer(substrate))

    # remove all assumed tags
    substrate = default_pattern.sub('', substrate)

    return responses, substrate.strip()


def get_unsent_codes(form, response_keys):
    groups = [
        g.get('name') for g in form.data.get('groups')
        if 'groups' in form.data
    ]

    for group in groups:
        group_tags = set(form.get_group_tags(group))
        keys = set(response_keys)

        is_partial = keys < group_tags
        if is_partial:
            return sorted(group_tags.difference(keys))

    return None
