# -*- coding: utf-8 -*-
import operator as op

from arpeggio import PTNodeVisitor, visit_parse_tree
from arpeggio.cleanpeg import ParserPEG
from parsimonious.grammar import Grammar
import parsley
from sqlalchemy import Boolean, Integer, func


# TODO: Arpeggio's PEG syntaxes actually use the Python
# syntax belowdecks. Change this if we need to squeeze
# out more performance. It also supports case-insensitive
# matches for string and regex matching, which may be
# important
qa_grammar = '''
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

OPERATIONS = {
    '+': op.iadd,
    '-': op.isub,
    '*': op.imul,
    '/': op.itruediv,
    # This is commented because of how Arpeggio deals
    # with terminals that are not a choice of items
    # in a sequence
    # '^': func.pow,
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


class QATreeVisitor(PTNodeVisitor):
    def __init__(self, defaults=True, **kwargs):
        # you *NEED* to add the submission class for now
        # the alternative is dealing with a circular dependency
        self.submission_class = kwargs.pop('submission_class')
        self.form = kwargs.pop('form')
        super().__init__(defaults, **kwargs)

    def visit_number(self, node, children):
        return float(node.value)

    def visit_factor(self, node, children):
        if len(children) == 1:
            return children[0]
        multiplier = -1 if children[0] == '-' else 1
        return multiplier * children[-1]

    # def visit_attribute(self, node, children):
    #     attribute_name = node.value[1:]
    #     return getattr(Submission, attribute_name)

    def visit_variable(self, node, children):
        var_name = node.value
        if var_name not in self.form.tags:
            raise ValueError('Variable ({}) not in form'.format(var_name))

        field = self.form.get_field_by_tag(var_name)
        cast_type = FIELD_TYPE_CASTS.get(field['type'])
        if cast_type is not None:
            return self.submission_class.data[var_name].astext.cast(cast_type)
        return self.submission_class.data[var_name]

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


def generate_qa_query(expression, form):
    from apollo.models import Submission

    parser = ParserPEG(qa_grammar, 'qa')
    try:
        tree = parser.parse(expression)
    except Exception:
        return None

    visitor = QATreeVisitor(form=form, submission_class=Submission)
    return visit_parse_tree(tree, visitor)


def calculate(start, pairs):
    result = start
    operators = {
        '+': op.add, '-': op.sub, '*': op.mul, '/': op.truediv, '^': op.pow,
        '>': op.gt, '>=': op.ge, '<': op.lt, '<=': op.le, '==': op.eq, '!=': op.ne,
        '||': op.or_, '&&': op.and_}

    for operator, value in pairs:
        if operator in operators:
            result = operators[operator](result, value)

    return result


def getvalue(submission, tag):
    if tag not in submission.data:
        raise AttributeError

    value = submission.data.get(tag)
    if value is None:
        raise AttributeError

    return value


def grammar_factory(env={}):
    return parsley.makeGrammar("""
dot = '.'
number = <digit+dot{0,1}digit*>:val -> float(val) if "." in val else int(val)
null = 'null' -> None
variable = <letter+>:var -> getvalue(env, var)
attribute = exactly('$')<anything+>:attr -> int(reduce(
    lambda obj, attr: getattr(obj, attr, None), [env] + attr.split('.')))
parens = '(' ws expr:e ws ')' -> e
value = null | number | variable | attribute | parens

add = '+' ws expr3:n -> ('+', n)
sub = '-' ws expr3:n -> ('-', n)
mul = '*' ws expr4:n -> ('*', n)
div = '/' ws expr4:n -> ('/', n)
pow = '^' ws value:n -> ('^', n)
gt  = '>' ws expr2:n -> ('>', n)
gte = '>=' ws expr2:n -> ('>=', n)
lt  = '<' ws expr2:n -> ('<', n)
lte = '<=' ws expr2:n -> ('<=', n)
eq  = '==' ws expr2:n -> ('==', n)
ne  = '!=' ws expr2:n -> ('!=', n)
or  = '||' ws expr1:n -> ('||', n)
and = '&&' ws expr1:n -> ('&&', n)

addsub = ws (add | sub)
muldiv = ws (mul | div)
power  = ws pow
comparison = ws (gt | gte | lt | lte | eq | ne)
logic  = ws (or | and)

expr = expr1:left logic*:right -> calculate(left, right)
expr1 = expr2:left comparison*:right -> calculate(left, right)
expr2 = expr3:left addsub*:right -> calculate(left, right)
expr3 = expr4:left muldiv*:right -> calculate(left, right)
expr4 = value:left power*:right -> calculate(left, right)
""", {'env': env, 'calculate': calculate, 'getvalue': getvalue})


# Parsers for Checklist Verification
class Comparator(object):
    def __init__(self):
        self.param = None

    def parse(self, source):
        grammar = '\n'.join(v.__doc__ for k, v in list(vars(self.__class__).items())
                            if '__' not in k and hasattr(v, '__doc__')
                            and v.__doc__)
        return Grammar(grammar).parse(source)

    def eval(self, source, param=None):
        if param is not None:
            self.param = float(param)
        node = self.parse(source) if isinstance(source, str) \
            or isinstance(source, str) else source
        method = getattr(self, node.expr_name, lambda node, children: children)
        return method(node, [self.eval(n) for n in node])

    def expr(self, node, children):
        'expr = operator _ operand'
        operator, _, operand = children
        return operator(self.param, operand)

    def operator(self, node, children):
        'operator = ">=" / "<=" / ">" / "<" / "=" / "!="'
        operators = {
            '>': op.gt, '>=': op.ge,
            '<': op.lt, '<=': op.le,
            '=': op.eq, '!=': op.ne}
        return operators[node.text]

    def operand(self, node, children):
        'operand = ~"\-?[0-9\.]+" / "True" / "False"'
        if node.text == "True":
            return True
        elif node.text == "False":
            return False
        else:
            return float(node.text)

    def _(self, node, children):
        '_ = ~"\s*"'
        pass
