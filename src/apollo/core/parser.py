from __future__ import unicode_literals
import re
import pyparsing as pp

PARSE_OK = 0
PARSE_UNEXPECTED_INPUT = 1
PARSE_MULTIPLE_ENTRY = 2

makeInt = lambda t: int(t[0])


def get_field_grammar(field):
    tag = pp.CaselessLiteral(field.name)

    if field.represents_boolean:
        grammar = tag.setParseAction(lambda t: True)
    elif field.allows_multiple_values:
        grammar = tag + pp.OneOrMore(
            pp.Word(pp.nums, exact=1).setParseAction(makeInt)
        )
    else:
        grammar = tag + pp.Word(pp.nums).setParseAction(makeInt)

    return grammar


def parse(form, text):
    status = PARSE_OK
    if form.form_type == 'CHECKLIST':
        g = pp.Regex(r'[a-z]{1,2}\d+', re.I)
    else:
        g = pp.Word(pp.alphas, exact=1)

    # get everything that looks like a tag
    tag_pairs = [item[0] for item in g.searchString(text)]

    # and replace everything that was found
    rpl = re.compile('|'.join((re.escape(t) for t in tag_pairs)))
    remainder = rpl.sub('', text)

    if remainder:
        # we're not supposed to have anything left over
        status = PARSE_UNEXPECTED_INPUT

    submission_data = {}
    cojoined_pairs = ''.join(tag_pairs)
    grammar_set = {
        field.name: get_field_grammar for group in form.groups for field in group.fields}

    for tag, grammar in grammar_set.iteritems():
        result = grammar.searchString(cojoined_pairs)
        if not result:
            continue

        if len(result) > 1:
            # someone entered a tag more than once
            status = PARSE_MULTIPLE_ENTRY

        for match in result:
            # really shouldn't have to do this more than once
            submission_data.update(tag=match[0])

        # remove matched text from search string
        cojoined_pairs = re.sub(
            r'{}\d*'.format(tag),
            '',
            cojoined_pairs,
            re.I
        )

    return submission_data, status
