# -*- coding: utf-8 -*-
from arpeggio import PTNodeVisitor
from arpeggio.cleanpeg import ParserPEG
from sqlalchemy import and_, or_

NUMBER_GRAMMAR = '''
number = r'\+{0,1}[0-9]+'
factor = number / '(' expression ')'
term = factor ('and' factor)*
expression = term ('or' term)*
search = expression+ EOF
'''

number_parser = ParserPEG(NUMBER_GRAMMAR, 'search', ignore_case=True)


class NumberSearchVisitor(PTNodeVisitor):
    def __init__(self, defaults=True, **kwargs):
        self.inbound_message_class = kwargs.pop('inbound_message_class')
        self.outbound_message_class = kwargs.pop('outbound_message_class')

        super().__init__(defaults, **kwargs)

    def visit_number(self, node, children):
        num_spec = f"%{node.value.replace('+', '')}%"
        return or_(
            self.inbound_message_class.recipient.ilike(num_spec),
            self.outbound_message_class.recipient.ilike(num_spec))

    def visit_term(self, node, children):
        return and_(*children)

    def visit_expression(self, node, children):
        return or_(*children)
