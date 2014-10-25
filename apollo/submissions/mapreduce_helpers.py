from itertools import izip_longest
from string import Template
from apollo.formsframework.parser import ExpressionParser


check_template = Template('''
function checkMissing(doc) {
    if ($conditions) {
        return true;
    }

    return false;
}
''')

evaluation_template = Template('''
function checkVerificationStatus(doc) {
    if checkMissing(doc) {
        return {missing: 1};
    }

    if ($lvalue $comparator $rvalue)
}
''')


def create_missing_check(operands):
    conditions = []
    for operand in operands:
        if operand.isalpha():
            conditions.append('doc.{} == null'.format(operand))

    if conditions:
        return check_template.substitute(conditions='||'.join(conditions))
    return check_template.substitute(conditions='false')


def create_expression_evaluator(expression):
    tokens = ExpressionParser(expression).entries
