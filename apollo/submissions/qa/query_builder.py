# -*- coding: utf-8 -*-
'''Query builder module for checklist QA'''

import operator as op

from arpeggio import PTNodeVisitor, visit_parse_tree
from arpeggio.cleanpeg import ParserPEG
from sqlalchemy import Boolean, Integer, and_, case, func

from apollo.models import Location, Participant, Submission

# NOTE: Arpeggio has 3 ways to represent a grammar:
#   - a Python syntax (the canonical)
#   - two similar, but slightly EBNF-ish syntaxes
# The EBNF/PEG syntaxes are converted to the canonical
# syntax (serious dogfooding) internally, but they are less
# verbose than it is.
# If we need the performance gain, this should be changed
# to the Python syntax. Other advantages of the Python
# syntax include case-insensitivty for regex and string
# matches
GRAMMAR = '''
number = r'\d+\.{0,1}\d*'
variable = r'[A-Z]+'
name = r'[a-zA-Z_][a-zA-Z0-9_]*'
lookup = "$" ("location" / "participant") ("." / "@") name
null = "NULL"
factor = ("+" / "-")? (number / variable / lookup / "(" expression ")")
value = null / factor
exponent = value (("^") value)*
product = exponent (("*" / "/") exponent)*
sum = product (("+" / "-") product)*
comparison = sum ((">=" / ">" / "<=" / "<" / "=" / "!=") sum)*
expression = comparison (("&&" / "||") comparison)*
qa = expression+ EOF
'''

# There's no entry for '^' because Arpeggio doesn't return
# terminals if they are not a choice of options when visiting
OPERATIONS = {
    '+': op.iadd,
    '-': op.isub,
    '*': op.imul,
    '/': op.itruediv,
    '>=': op.ge,
    '>': op.gt,
    '<=': op.le,
    '<': op.lt,
    '=': op.eq,
    '!=': op.ne,
    '&&': op.and_,
    '||': op.or_
}

FIELD_TYPE_CASTS = {
    'boolean': Boolean,
    'integer': Integer,
    'select': Integer
}


class BaseVisitor(PTNodeVisitor):
    def visit_number(self, node, children):
        return float(node.value)

    def visit_factor(self, node, children):
        if len(children) == 1:
            return children[0]
        multiplier = -1 if children[0] == '-' else 1
        return multiplier * children[-1]

    def visit_value(self, node, children):
        return children[-1]

    def visit_exponent(self, node, children):
        if len(children) == 1:
            return children[0]

        exponent = children[0]
        for i in children[1:]:
            # exponent **= i
            exponent = func.pow(exponent, i)

        return exponent

    def visit_product(self, node, children):
        product = children[0]
        for i in range(2, len(children), 2):
            sign = children[i - 1]
            product = OPERATIONS[sign](product, children[i])

        return product

    def visit_sum(self, node, children):
        total = children[0]
        for i in range(2, len(children), 2):
            sign = children[i - 1]
            total = OPERATIONS[sign](total, children[i])

        return total

    def visit_comparison(self, node, children):
        comparison = children[0] if children[0] != 'NULL' else None
        for i in range(2, len(children), 2):
            sign = children[i - 1]
            item = None if children[i] == 'NULL' else children[i]
            comparison = OPERATIONS[sign](comparison, item)

        return comparison

    def visit_expression(self, node, children):
        expression = children[0] if children[0] != 'NULL' else None
        for i in range(2, len(children), 2):
            sign = children[i - 1]
            expression = OPERATIONS[sign](expression, children[i])

        return expression


class InlineQATreeVisitor(BaseVisitor):
    def __init__(self, defaults=True, **kwargs):
        self.form = kwargs.pop('form')
        self.submission = kwargs.pop('submission')
        super().__init__(defaults, **kwargs)

    def visit_variable(self, node, children):
        var_name = node.value
        if var_name not in self.form.tags:
            raise ValueError('Variable ({}) not in form'.format(var_name))

        return self.submission.data.get(var_name, 'NULL')

    def visit_lookup(self, node, children):
        top_level_attr, symbol, name = children

        attribute = getattr(self.submission, top_level_attr)

        if symbol == '.':
            return getattr(attribute, name)
        else:
            return attribute.extra_data.get(name)


class QATreeVisitor(BaseVisitor):
    def __init__(self, defaults=True, **kwargs):
        self.form = kwargs.pop('form')
        super().__init__(defaults, **kwargs)

    def visit_lookup(self, node, children):
        top_level_attr, symbol, name = children

        if top_level_attr == 'location':
            if symbol == '.':
                return getattr(Location, name)
            else:
                return Location.extra_data[name]
        else:
            if symbol == '.':
                return getattr(Participant, name)
            else:
                return Participant.extra_data[name]

    def visit_variable(self, node, children):
        var_name = node.value
        if var_name not in self.form.tags:
            raise ValueError('Variable ({}) not in form'.format(var_name))

        # casting is necessary because PostgreSQL will throw
        # a fit if you attempt some operations that mix JSONB
        # with other types
        field = self.form.get_field_by_tag(var_name)
        cast_type = FIELD_TYPE_CASTS.get(field['type'])

        if cast_type is not None:
            return Submission.data[var_name].astext.cast(cast_type)
        return Submission.data[var_name]


def generate_qa_query(expression, form):
    parser = ParserPEG(GRAMMAR, 'qa')
    tree = parser.parse(expression)

    visitor = QATreeVisitor(form=form)

    return visit_parse_tree(tree, visitor)


def get_logical_check_stats(query, form, check):
    complete_expression = '{lvalue} {comparator} {rvalue}'.format(**check)
    qa_query = generate_qa_query(complete_expression, form)

    # add joins as necessary
    if '$location' in complete_expression:
        query = query.join(Location, Location.id == Submission.location_id)

    if '$participant' in complete_expression:
        query = query.join(Participant, Participant.id == Submission.participant_id)

    qa_case_query = case([
        (qa_query == True, 'OK'),
        (and_(qa_query == False, Submission.verification_status == Submission.VERIFICATION_STATUSES[1][0]), 'Verified'),    # noqa
        (and_(qa_query == False, Submission.verification_status != Submission.VERIFICATION_STATUSES[1][0]), 'Flagged'),     # noqa
        (qa_query == None, 'Missing')
    ])

    return query.with_entities(
        qa_case_query.label('status'),
        func.count(qa_case_query)).group_by('status').all()


def get_inline_qa_status(submission, check):
    check_expression = '{lvalue} {comparator} {rvalue}'.format(**check)

    parser = ParserPEG(GRAMMAR, 'qa')
    tree = parser.parse(check_expression)

    visitor = InlineQATreeVisitor(form=submission.form, submission=submission)

    try:
        result = visit_parse_tree(tree, visitor)
    except TypeError:
        # tried to perform a math operation combining None and a number,
        # most likely
        return None

    return result
