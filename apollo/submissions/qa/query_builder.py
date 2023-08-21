# -*- coding: utf-8 -*-
'''Query builder module for checklist QA'''

import operator as op

from arpeggio import PTNodeVisitor, visit_parse_tree
from arpeggio.cleanpeg import ParserPEG
from sqlalchemy import (
    BigInteger, Integer, String, and_, case, cast, false, func, null, or_)
from sqlalchemy.dialects.postgresql import array
from sqlalchemy.sql.operators import concat_op

from apollo.models import Location, Participant, Submission
from apollo.submissions.models import QUALITY_STATUSES

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
lookup = "$" ("location" / "participant" / "submission") ("." / "@") name
null = "NULL"
factor = ("+" / "-")? (number / variable / lookup / "(" expression ")")
value = null / factor
exponent = value (("^") value)*
product = exponent (("*" / "/") exponent)*
sum = product (("+" / "-") product)*
concat = sum (("|") sum)*
comparison = concat ((">=" / ">" / "<=" / "<" / "=" / "!=") concat)*
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
    'select': Integer,
    'string': String,
}


def _get_cast_type(field):
    if field['type'] in FIELD_TYPE_CASTS:
        return FIELD_TYPE_CASTS.get(field['type'])

    if field['type'] == 'integer':
        if len(str(field['max'])) > 9 or len(str(field['min'])) > 9:
            return BigInteger

        return Integer

    return null()


class BaseVisitor(PTNodeVisitor):
    def __init__(self, defaults=True, **kwargs):

        super().__init__(defaults, **kwargs)

    def visit_number(self, node, children):
        if node.value.isdigit():
            return int(node.value)
        else:
            return float(node.value)

    def visit_factor(self, node, children):
        if len(children) == 1:
            return children[0]
        multiplier = -1 if children[0] == '-' else 1
        return multiplier * children[-1]

    def visit_value(self, node, children):
        return children[-1]

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

    def visit_concat(self, node, children):
        if len(children) == 1:
            return children[0]

        self.uses_concat = True

        operand = func.cast(children[0], String)
        for i in children[1:]:
            operand = concat_op(operand, func.cast(i, String))

        return operand

    def visit_comparison(self, node, children):
        if getattr(self, 'uses_concat', False):
            comparison = func.cast(children[0], String) \
                if children[0] != 'NULL' else None
        else:
            comparison = children[0] if children[0] != 'NULL' else None
        for i in range(2, len(children), 2):
            sign = children[i - 1]
            if getattr(self, 'uses_concat', False):
                item = func.cast(children[i], String) \
                    if children[i] != 'NULL' else None
            else:
                item = children[i] if children[i] != 'NULL' else None
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
            return 'NULL'

        field = self.form.get_field_by_tag(var_name)
        if field['type'] == 'multiselect':
            return 'NULL'

        return self.submission.data.get(var_name, 'NULL')

    def visit_lookup(self, node, children):
        top_level_attr, symbol, name = children

        if top_level_attr in ['location', 'participant']:
            attribute = getattr(self.submission, top_level_attr)

            if symbol == '.':
                return getattr(attribute, name)
            else:
                return attribute.extra_data.get(name)
        else:
            return getattr(self.submission, name)

    def visit_comparison(self, node, children):
        if len(children) > 1:
            # left and right are indices 0 and 2 respectively
            left = children[0]
            right = children[2]
            if isinstance(left, str) and isinstance(right, str):
                # both sides are NULL
                return 'NULL'
        return super().visit_comparison(node, children)


class QATreeVisitor(BaseVisitor):
    def __init__(self, defaults=True, **kwargs):
        self.prev_cast_type = None
        self.lock_null = False
        self.form = kwargs.pop('form')
        self.variables = set()
        super().__init__(defaults, **kwargs)

    def visit_lookup(self, node, children):
        top_level_attr, symbol, name = children

        if top_level_attr == 'location':
            if symbol == '.':
                return getattr(Location, name).cast(BigInteger)
            else:
                return Location.extra_data[name].astext.cast(BigInteger)
        elif top_level_attr == 'participant':
            if symbol == '.':
                return getattr(Participant, name).cast(BigInteger)
            else:
                return Participant.extra_data[name].astext.cast(BigInteger)
        else:
            return getattr(Submission, name).cast(BigInteger)

    def visit_variable(self, node, children):
        var_name = node.value
        self.variables.add(var_name)
        if var_name not in self.form.tags:
            self.lock_null = True
            return null()

        # casting is necessary because PostgreSQL will throw
        # a fit if you attempt some operations that mix JSONB
        # with other types
        field = self.form.get_field_by_tag(var_name)

        if field['type'] == 'multiselect':
            self.lock_null = True
            return null()

        cast_type = _get_cast_type(field)
        if cast_type not in (BigInteger, Integer, String):
            self.lock_null = True

        # there are side effects when attempting to make comparisons
        # between attributes of different types. Naturally, you wouldn't
        # be able to do that but we have no way of knowing if a user will
        # make that attempt. This snippet helps to prevent that from
        # occurring by tracking the types and whenever it notices there's
        # a difference, it would start outputting nulls so the query
        # returns no result.
        if (
            (
                self.prev_cast_type is not None and
                (self.prev_cast_type != cast_type)
            ) or self.lock_null
        ):
            self.lock_null = True
            return null()
        else:
            self.prev_cast_type = cast_type
            if cast_type in (BigInteger, Integer):
                return cast(
                    func.nullif(Submission.data[var_name].astext, ''),
                    cast_type)
            elif cast_type is not None:
                return Submission.data[var_name].astext.cast(cast_type)
            return Submission.data[var_name]


def generate_qa_query(expression, form):
    # short-circuit for empty expressions
    if expression == '' or expression == "=":
        return null(), set()

    parser = ParserPEG(GRAMMAR, 'qa')
    tree = parser.parse(expression)

    visitor = QATreeVisitor(form=form)

    return visit_parse_tree(tree, visitor), visitor.variables


def generate_qa_queries(form):
    subqueries = []
    tag_groups = []
    if form.quality_checks:
        for check in form.quality_checks:
            expression = build_expression(check)
            uses_null = 'null' in expression.lower()

            # evaluate every expression, including empty ones
            subquery, used_tags = generate_qa_query(expression, form)

            tags = array(used_tags)

            if used_tags:
                null_query = or_(*[
                    Submission.data[tag] == None for tag in used_tags   # noqa
                ]) if not uses_null else false()
                case_query = case([
                    (and_(null_query == False, subquery == True, ~Submission.verified_fields.has_all(tags)), 'Flagged'),  # noqa
                    (and_(null_query == False, subquery == True, Submission.verified_fields.has_all(tags)), 'Verified'),   # noqa
                    (and_(null_query == False, subquery == False), 'OK'), # noqa
                    (or_(null_query == True, subquery == None), 'Missing')   # noqa
                ]).label(check['name'])
            else:
                case_query = case([
                    (subquery == True, 'Flagged'),   # noqa
                    (subquery == False, 'OK')   # noqa
                ]).label(check['name'])

            subqueries.append(case_query)
            tag_groups.append(sorted(used_tags))

    return subqueries, tag_groups


def get_logical_check_stats(query, form, condition):
    complete_expression = build_expression(condition)
    # short-circuit for empty QA
    if complete_expression == '':
        return [('Missing', query.count())]

    qa_query, question_codes = generate_qa_query(complete_expression, form)

    # add joins as necessary
    if '$location' in complete_expression:
        query = query.join(Location, Location.id == Submission.location_id)

    if '$participant' in complete_expression:
        query = query.join(
            Participant, Participant.id == Submission.participant_id)

    if 'null' in complete_expression.lower():
        null_query = or_(*[
            Submission.data[tag] == None    # noqa
            for tag in question_codes
        ]) if question_codes else false()
    else:
        null_query = false()

    if question_codes:
        qa_case_query = case([
            (and_(null_query == False, qa_query == True, ~Submission.verified_fields.has_all(array(question_codes))), 'Flagged'),   # noqa
            (and_(null_query == False, qa_query == True, Submission.verified_fields.has_all(array(question_codes))), 'Verified'),   # noqa
            (and_(null_query == False, qa_query == False), 'OK'),   # noqa
            (or_(null_query == False, qa_query == None), 'Missing') # noqa
        ])
    else:
        qa_case_query = case([
            (qa_query == True, 'Flagged'),  # noqa
            (qa_query == False, 'OK')
        ])

    return query.with_entities(
        qa_case_query.label('status'),
        func.count(qa_case_query)).group_by('status').all()


class TagVisitor(PTNodeVisitor):
    def __init__(self, *args, **kwargs):
        self.variables = set()
        super().__init__(*args, **kwargs)

    def visit_variable(self, node, children):
        self.variables.add(node.value)


def get_inline_qa_status(submission, condition):
    control_expression = build_expression(condition)

    # short-circuit for empty expression
    if control_expression == '':
        return None, set()

    parser = ParserPEG(GRAMMAR, 'qa')
    tree = parser.parse(control_expression)

    var_visitor = TagVisitor()
    visit_parse_tree(tree, var_visitor)

    used_tags = var_visitor.variables.intersection(submission.form.tags)

    visitor = InlineQATreeVisitor(form=submission.form, submission=submission)

    try:
        result = visit_parse_tree(tree, visitor)
    except TypeError:
        # tried to perform a math operation combining None and a number,
        # most likely
        return None, set()

    return result, used_tags


def build_expression(logical_check):
    if 'criteria' in logical_check:
        control_expression = ''

        for index, cond in enumerate(logical_check['criteria']):
            if index:
                control_expression += '{conjunction} {lvalue} {comparator} {rvalue} '.format(**cond)  # noqa
            else:
                control_expression += '{lvalue} {comparator} {rvalue} '.format(**cond)  # noqa
    else:
        control_expression = '{lvalue} {comparator} {rvalue} '.format(**logical_check)  # noqa

    return control_expression.strip()


def qa_status(submission, check):
    result, tags = get_inline_qa_status(submission, check)
    verified_fields = submission.verified_fields or set()
    if result is True and not tags.issubset(verified_fields):
        return QUALITY_STATUSES['FLAGGED']
    elif result is True and tags.issubset(verified_fields):
        return QUALITY_STATUSES['VERIFIED']
    elif result is False:
        return QUALITY_STATUSES['OK']
    else:
        return None
