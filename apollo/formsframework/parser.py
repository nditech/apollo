# -*- coding: utf-8 -*-

import operator as op
from parsimonious.grammar import Grammar
import parsley


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


def getvalue(obj, var):
    if getattr(obj, var) or getattr(obj, var) == 0:
        return getattr(obj, var)
    else:
        raise AttributeError


def grammar_factory(env={}):
    return parsley.makeGrammar("""
dot = '.'
number = <digit+dot{0,1}digit*>:val -> float(val) if "." in val else int(val)
variable = <letter+>:var -> getvalue(env, var)
attribute = exactly('$')<anything+>:attr -> int(reduce(
    lambda obj, attr: getattr(obj, attr, None), [env] + attr.split('.')))
parens = '(' ws expr:e ws ')' -> e
value = number | variable | attribute | parens

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
