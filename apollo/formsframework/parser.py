from __future__ import division
import operator as op
from parsimonious.grammar import Grammar
import parsley


def calculate(start, pairs):
    result = start
    operators = {
        '+': op.add, '-': op.sub, '*': op.mul, '/': op.truediv, '^': op.pow}

    for operator, value in pairs:
        if operator in operators:
            result = operators[operator](result, value)

    return result

def getvalue(obj, var):
    if getattr(obj, var):
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

add = '+' ws expr2:n -> ('+', n)
sub = '-' ws expr2:n -> ('-', n)
mul = '*' ws expr3:n -> ('*', n)
div = '/' ws expr3:n -> ('/', n)
pow = '^' ws value:n -> ('^', n)

addsub = ws (add | sub)
muldiv = ws (mul | div)

expr = expr2:left addsub*:right -> calculate(left, right)
expr2 = expr3:left muldiv*:right -> calculate(left, right)
expr3 = value:left pow*:right -> calculate(left, right)
""", {'env': env, 'calculate': calculate, 'getvalue': getvalue})


# Parsers for Checklist Verification
class Comparator(object):
    def __init__(self):
        self.param = None

    def parse(self, source):
        grammar = '\n'.join(v.__doc__ for k, v in vars(self.__class__).items()
                            if '__' not in k and hasattr(v, '__doc__')
                            and v.__doc__)
        return Grammar(grammar).parse(source)

    def eval(self, source, param=None):
        if param is not None:
            self.param = float(param)
        node = self.parse(source) if isinstance(source, str) \
            or isinstance(source, unicode) else source
        method = getattr(self, node.expr_name, lambda node, children: children)
        return method(node, [self.eval(n) for n in node])

    def expr(self, node, children):
        'expr = operator _ number'
        operator, _, number = children
        return operator(self.param, number)

    def operator(self, node, children):
        'operator = ">=" / "<=" / ">" / "<" / "=" / "!="'
        operators = {
            '>': op.gt, '>=': op.ge,
            '<': op.lt, '<=': op.le,
            '=': op.eq, '!=': op.ne}
        return operators[node.text]

    def number(self, node, children):
        'number = ~"\-?[0-9\.]+"'
        return float(node.text)

    def _(self, node, children):
        '_ = ~"\s*"'
        pass
