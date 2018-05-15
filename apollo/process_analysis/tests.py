# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from unittest import TestCase
from apollo.process_analysis.common import (
    dataframe_analysis, multiselect_dataframe_analysis,
    make_histogram, summarize_options, percent_of,
    generate_numeric_field_stats, generate_single_choice_field_stats,
    generate_mutiple_choice_field_stats, generate_incident_field_stats,
    generate_field_stats
)


class ProcessAnalysisTest(TestCase):
    def setUp(self):
        self.df = pd.DataFrame({
            'location': ["A", "B", "B", "C", "D"],
            'AA': [1, 2, 3, 4, np.nan],
            'AB': [2, 3, 4, 5, 6],
            'AC': [[1, 2], [2, 4], [2, 3], [3], [5, 6]],
            'AD': [2, 2, 3, 3, 4]
        })

    def test_dataframe_analysis(self):
        func = dataframe_analysis

        # discrete tests
        self.assertEqual(
            func('discrete', self.df, 'AA')['value_counts'],
            {4.0: 1, 3.0: 1, 2.0: 1, 1.0: 1})
        self.assertEqual(
            func('discrete', self.df, 'AA')['value_counts_sum'],
            4)
        self.assertEqual(
            func('discrete', self.df, 'AA')['count'],
            4)
        self.assertEqual(
            func('discrete', self.df, 'AA')['size'],
            5)
        self.assertEqual(
            func('discrete', self.df, 'AA')['diff'],
            1)

        # scalar tests
        self.assertEqual(
            func('scalar', self.df, 'AB')['mean'],
            4.0)
        self.assertEqual(
            func('scalar', self.df, 'AB')['count'],
            5)
        self.assertEqual(
            func('scalar', self.df, 'AB')['size'],
            5)
        self.assertEqual(
            func('scalar', self.df, 'AB')['diff'],
            0)

    def test_multiselect_dataframe_analysis(self):
        options = [1, 2, 3, 4, 5, 6, 7]
        func = multiselect_dataframe_analysis

        self.assertEqual(
            func(self.df, 'AC', options)['value_counts'],
            {1: 1, 2: 3, 3: 2, 4: 1, 5: 1, 6: 1, 7: 0})

        self.assertEqual(
            func(self.df, 'AC', options)['value_counts_sum'],
            5)

        self.assertEqual(
            func(self.df, 'AC', options)['count'],
            5)

        self.assertEqual(
            func(self.df, 'AC', options)['size'],
            5)

        self.assertEqual(
            func(self.df, 'AC', options)['diff'],
            0)

    def test_generate_numeric_field_stats(self):
        self.assertEqual(
            generate_numeric_field_stats('AA', self.df),
            {'type': 'numeric', 'reported': 4, 'missing': 1,
                'percent_reported': 80.0, 'percent_missing': 20.0, 'mean': 2.5,
                'std': 1.118033988749895})
        self.assertEqual(
            generate_numeric_field_stats('AA', self.df.groupby('location')),
            {'type': 'numeric', 'locations':
             {'A': {'mean': 1.0, 'std': 0.0, 'reported': 1, 'missing': 0,
                    'percent_reported': 100.0, 'percent_missing': 0.0},
              'B': {'mean': 2.5, 'std': 0.7071067811865476, 'reported': 2,
                    'missing': 0, 'percent_reported': 100.0,
                    'percent_missing': 0.0},
              'C': {'mean': 4.0, 'std': 0.0, 'reported': 1, 'missing': 0,
                    'percent_reported': 100.0, 'percent_missing': 0.0},
              'D': {'mean': 0.0, 'std': 0.0, 'reported': 0, 'missing': 1,
                    'percent_reported': 0.0, 'percent_missing': 100.0}}})

    def test_generate_single_choice_field_stats(self):
        self.assertEqual(
            generate_single_choice_field_stats('AB', self.df, [2, 3, 4, 5, 6]),
            {'type': 'single-choice', 'labels': None, 
             'histogram': [(1, 20.0), (1, 20.0), (1, 20.0), (1, 20.0),
                           (1, 20.0)],
             'reported': 5, 'missing': 0, 'percent_reported': 100.0,
             'percent_missing': 0.0, 'total': 5})
        self.assertEqual(
            generate_single_choice_field_stats(
                'AB', self.df.groupby('location'), [2, 3, 4, 5, 6]),
            {'type': 'single-choice', 'labels': None, 'locations':
             {'A': {'missing': 0, 'reported': 1, 'total': 1, 
                    'percent_reported': 100.0, 'percent_missing': 0.0,
                    'histogram': [(1, 100.0), (0, 0.0), (0, 0.0),
                                  (0, 0.0), (0, 0.0)]},
              'B': {'missing': 0, 'reported': 2, 'total': 2,
                    'percent_reported': 100.0, 'percent_missing': 0.0,
                    'histogram': [(0, 0.0), (1, 50.0), (1, 50.0),
                                  (0, 0.0), (0, 0.0)]},
              'C': {'missing': 0, 'reported': 1, 'total': 1,
                    'percent_reported': 100.0, 'percent_missing': 0.0,
                    'histogram': [(0, 0.0), (0, 0.0), (0, 0.0),
                                  (1, 100.0), (0, 0.0)]},
              'D': {'missing': 0, 'reported': 1, 'total': 1,
                    'percent_reported': 100.0, 'percent_missing': 0.0,
                    'histogram': [(0, 0.0), (0, 0.0), (0, 0.0),
                                  (0, 0.0), (1, 100.0)]}}})

    def test_generate_mutiple_choice_field_stats(self):
        opt = [1, 2, 3, 4, 5, 6]
        self.assertEqual(
            generate_mutiple_choice_field_stats('AC', self.df, opt),
            {'type': 'multiple-choice',
             'histogram': [(1, 20.0), (3, 60.0), (2, 40.0),
                           (1, 20.0), (1, 20.0), (1, 20.0)],
             'reported': 5, 'missing': 0, 'percent_reported': 100.0,
             'percent_missing': 0.0, 'labels': None})
        self.assertEqual(
            generate_mutiple_choice_field_stats(
                'AC', self.df.groupby('location'),
                opt),
            {'type': 'multiple-choice', 'labels': None, 'locations':
             {'A': {'missing': 0, 'reported': 1, 'percent_reported': 100.0,
                    'percent_missing': 0.0,
                    'histogram': [(1, 100.0), (1, 100.0), (0, 0.0),
                                  (0, 0.0), (0, 0.0), (0, 0.0)]},
              'B': {'missing': 0, 'reported': 2, 'percent_reported': 100.0,
                    'percent_missing': 0.0,
                    'histogram': [(0, 0.0), (2, 100.0), (1, 50.0),
                                  (1, 50.0), (0, 0.0), (0, 0.0)]}, 
              'C': {'missing': 0, 'reported': 1, 'percent_reported': 100.0,
                    'percent_missing': 0.0,
                    'histogram': [(0, 0.0), (0, 0.0), (1, 100.0),
                                  (0, 0.0), (0, 0.0), (0, 0.0)]},
              'D': {'missing': 0, 'reported': 1, 'percent_reported': 100.0,
                    'percent_missing': 0.0,
                    'histogram': [(0, 0.0), (0, 0.0), (0, 0.0),
                                  (0, 0.0), (1, 100.0), (1, 100.0)]}}})

    def test_generate_incident_field_stats(self):
        self.assertEqual(
            generate_incident_field_stats('AA', self.df, None),
            {'type': 'incidents', 'labels': None, 'reported': 4, 'missing': 1,
             'percent_reported': 80.0, 'percent_missing': 20.0, 'total': 5})
        self.assertEqual(
            generate_incident_field_stats(
                'AA', self.df.groupby('location'), None),
            {'type': 'incidents', 'labels': None, 'locations': {
             'A': {'missing': 0, 'reported': 1, 'total': 1,
                   'percent_reported': 100.0, 'percent_missing': 0.0},
             'B': {'missing': 0, 'reported': 2, 'total': 2,
                   'percent_reported': 100.0, 'percent_missing': 0.0},
             'C': {'missing': 0, 'reported': 1, 'total': 1,
                   'percent_reported': 100.0, 'percent_missing': 0.0},
             'D': {'missing': 1, 'reported': 0, 'total': 1,
                   'percent_reported': 0.0, 'percent_missing': 100.0}}})

    def test_make_histogram(self):
        self.assertEqual(
            make_histogram([2, 3, 4], self.df.AD),
            [2, 2, 1])

    def test_summarize_options(self):
        self.assertEqual(
            summarize_options([2, 3, 4], self.df.AD),
            [2, 2, 1])

    def test_percent_of(self):
        self.assertEqual(
            percent_of(2, 10),
            20.0)
        self.assertEqual(
            percent_of(3, 0),
            0)

    def test_generate_field_stats(self):
        self.assertEqual(
            generate_field_stats(
                {'type': 'boolean', 'tag': 'AA'},
                self.df),
            {'type': 'incidents', 'labels': None, 'reported': 4, 'missing': 1,
             'percent_reported': 80.0, 'percent_missing': 20.0, 'total': 5})
