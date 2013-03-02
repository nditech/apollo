from djorm_expressions.base import SqlFunction
from djorm_expressions.tree import OperatorTree


class HstoreIntegerValue(SqlFunction):
    ''' This SqlFunction converts values in a Hstore
    to an integer, this is a special case function as
    we store list of integers as comma separated
    values. This function works by first converting
    both regular string integers and comma separated
    string integers to an array first and only selects
    the first value. This function isn't very useful
    for dealing with integer arrays that are stored
    in the hstore.'''
    sql_template = "(STRING_TO_ARRAY(%(field)s -> %%s, ',')::int[])[1]"


class PLUS(OperatorTree):
    _connector = "+"


class MINUS(OperatorTree):
    _connector = "-"


class EQUALS(OperatorTree):
    _connector = "="


class GT(OperatorTree):
    _connector = '>'


class GTE(OperatorTree):
    _connector = '>='


class LT(OperatorTree):
    _connector = '<'


class LTE(OperatorTree):
    _connector = '<='
