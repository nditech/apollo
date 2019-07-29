from unittest import TestCase

import numpy as np
import pandas as pd

from apollo.submissions.aggregation import (
    _multiselect_field_processor,
    _numeric_field_processor,
    _select_field_processor,
)
from apollo.submissions.incidents import incidents_csv
from apollo.submissions.qa.query_builder import build_expression


class IncidentsTest(TestCase):
    def setUp(self):
        self.df = pd.DataFrame({
            'location': ["A", "B", "B", "C", "D"],
            'AA': [1, 2, 3, 4, np.nan],
            'AB': [2, 3, 4, 5, 6],
            'AC': [[1, 2], [2, 4], [2, 3], [3], [5, 6]],
            'AD': [2, 2, 3, 3, 4]
        })

    def test_incidents_csv(self):
        self.assertEqual(
            incidents_csv(self.df, 'location', 'AA'),
            [{'LOC': 'A', 'TOT': 1, 'A': 0}, {'LOC': 'B', 'TOT': 5, 'A': 0},
             {'LOC': 'C', 'TOT': 4, 'A': 0}, {'LOC': 'D', 'TOT': 0, 'A': 0}])


class AggregationTest(TestCase):
    def test_numeric_field_aggregation(self):
        column = pd.Series([1, 3, 5, 2, None, 7, 4])
        result = _numeric_field_processor(column)
        self.assertEqual(result, 22)

    def test_select_field_aggregation(self):
        options = [1, 2, 3, 4, 5]
        column = pd.Series([5, 5, 5, 1, 2, None, 2, 4, 5, None])

        result = _select_field_processor(options, column)
        self.assertEqual(result, [1, 2, 0, 1, 4])

    def test_multiselect_field_aggregation(self):
        options = [1, 2, 3, 4, 5]
        column = pd.Series([
            [1, 5],
            [1, 2, 3, 4, 5],
            None,
            [2, 3],
            [3, 4, 5],
            [1, 2, 3, 4],
            None,
            None,
            [1, 2, 3, 4, 5],
            None
        ])

        result = _multiselect_field_processor(options, column)
        self.assertEqual(result, [4, 4, 5, 4, 4])


class ExpressionBuilderTestCase(TestCase):
    def test_single_check(self):
        valid_check = {'lvalue': 'AA', 'comparator': '=', 'rvalue': '1'}
        invalid_check = {'favourite_fruit': 'apples'}

        expression = build_expression(valid_check)
        self.assertEqual(expression, 'AA = 1')

        with self.assertRaises(KeyError):
            expression = build_expression(invalid_check)

    def test_multiple_checks(self):
        valid_checks = {
            'criteria': [
                {
                    'lvalue': 'AA', 'comparator': '=', 'rvalue': '1',
                    'conjunction': '&&'
                },
                {
                    'lvalue': 'BA', 'comparator': '=', 'rvalue': '1',
                    'conjunction': '&&'
                },
                {
                    'lvalue': 'BH', 'comparator': '=', 'rvalue': 'EJ',
                    'conjunction': '||'
                }
            ]
        }

        expression = build_expression(valid_checks)
        self.assertEqual(expression, 'AA = 1 && BA = 1 || BH = EJ')
