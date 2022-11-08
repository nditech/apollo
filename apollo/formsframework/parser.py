# -*- coding: utf-8 -*-
import operator as op

from parsimonious.grammar import Grammar
import parsley


def calculate(start, pairs):
    result = start
    operators = {
        '+': op.add, '-': op.sub, '*': op.mul, '/': op.truediv, '^': op.pow,
        '>': op.gt, '>=': op.ge, '<': op.lt, '<=': op.le, '==': op.eq,
        '!=': op.ne, '||': op.or_, '&&': op.and_}

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
        # using explicit raw-strings prevents a deprecation warning
        # caused by the parsing of the escape sequences
        grammar = r'''
            expr = operator _ operand
            operator = ">=" / "<=" / ">" / "<" / "=" / "!="
            operand = ~"\\-?[0-9\\.]+" / "True" / "False"
            _ = ~"\\s*"
        '''
        return Grammar(grammar).parse(source)

    def eval(self, source, param=None):
        if param is not None:
            self.param = float(param)
        node = self.parse(source) if isinstance(source, str) \
            or isinstance(source, str) else source
        method = getattr(self, node.expr_name, lambda node, children: children)
        return method(node, [self.eval(n) for n in node])

    def expr(self, node, children):
        operator, _, operand = children
        return operator(self.param, operand)

    def operator(self, node, children):
        operators = {
            '>': op.gt, '>=': op.ge,
            '<': op.lt, '<=': op.le,
            '=': op.eq, '!=': op.ne}
        return operators[node.text]

    def operand(self, node, children):
        if node.text == "True":
            return True
        elif node.text == "False":
            return False
        else:
            return float(node.text)

    def _(self, node, children):
        pass
