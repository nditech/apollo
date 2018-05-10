# -*- coding: utf-8 -*-
'''Query builder module for checklist QA'''

import operator as op

from arpeggio import PTNodeVisitor, visit_parse_tree
from arpeggio.cleanpeg import ParserPEG
from sqlalchemy import Boolean, Integer, and_, case, func

from apollo.submissions.models import Submission

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
attribute = r'\$[a-zA-Z_][a-zA-Z0-9_]*'
null = "NULL"
factor = ("+" / "-")? (number / variable / attribute / "(" expression ")")
value = null / factor
exponent = value (("^") value)*
product = exponent (("*" / "/") exponent)*
sum = product (("+" / "-") product)*
comparison = sum ((">=" / ">" / "<=" / "<" / "==" / "!=") sum)*
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
    '==': op.eq,
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
        comparison = children[0]
        for i in range(2, len(children), 2):
            sign = children[i - 1]
            item = None if children[i] == 'NULL' else children[i]
            comparison = OPERATIONS[sign](comparison, item)

        return comparison

    def visit_expression(self, node, children):
        if len(children) == 1 and children[0] == 'NULL':
            return None
        expression = children[0]
        for i in range(2, len(children), 2):
            sign = children[i - 1]
            expression = OPERATIONS[sign](expression, children[i])

        return expression


class InlineQATreeVisitor(BaseVisitor):
    def __init__(self, defaults=True, **kwargs):
        self.form = kwargs.pop('form')
        self.submission = kwargs.pop('submission')

    def visit_variable(self, node, children):
        var_name = node.value
        if var_name not in self.form.tags:
            raise ValueError('Variable ({}) not in form'.format(var_name))

        # casting is necessary because PostgreSQL will throw
        # a fit if you attempt some operations that mix JSONB
        # with other types
        field = self.form.get_field_by_tag(var_name)
        return self.submission.data.get(field)


class QATreeVisitor(BaseVisitor):
    def __init__(self, defaults=True, **kwargs):
        self.form = kwargs.pop('form')
        super().__init__(defaults, **kwargs)

    # def visit_attribute(self, node, children):
    #     attribute_name = node.value[1:]
    #     return getattr(Submission, attribute_name)

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
    try:
        tree = parser.parse(expression)
    except Exception:
        raise

    try:
        visitor = QATreeVisitor(form=form)
    except Exception:
        raise

    return visit_parse_tree(tree, visitor)


def get_logical_check_stats(query, form, check):
    complete_expression = '{} {} {}'.format(
        check['lvalue'], check['comparator'], check['rvalue'])
    qa_query = generate_qa_query(complete_expression, form)

    qa_case_query = case([
        (qa_query == True, 'OK'),
        (and_(qa_query == False, Submission.verification_status == Submission.VERIFICATION_STATUSES[1][0]), 'Verified'),    # noqa
        (and_(qa_query == False, Submission.verification_status != Submission.VERIFICATION_STATUSES[1][0]), 'Flagged'),     # noqa
        (qa_query == None, 'Missing')
    ])

    return query.with_entities(
        qa_case_query.label('status'),
        func.count(qa_case_query)).group_by('status').all()
