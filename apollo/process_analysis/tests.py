# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from unittest import TestCase
from apollo.process_analysis.common import (
    percent_of,
    generate_mean_stats,
    generate_histogram_stats,
    generate_multiselect_histogram_stats,
    generate_count_stats,
    generate_field_stats,
)


class ProcessAnalysisTest(TestCase):
    def setUp(self):
        self.df = pd.DataFrame(
            {
                "location": ["A", "B", "B", "C", "D"],
                "AA": [1, 2, 3, 4, np.nan],
                "AB": [2, 3, 4, 5, 6],
                "AC": [[1, 2], [2, 4], [2, 3], [3], [5, 6]],
                "AD": [2, 2, 3, 3, 4],
            }
        )

        self.maxDiff = None

    def test_generate_mean_stats(self):
        self.assertDictEqual(
            generate_mean_stats("AA", self.df),
            {
                "type": "mean",
                "reported": 4,
                "available": 4,
                "not_available": 0,
                "missing": 1,
                "percent_reported": 80.0,
                "percent_missing": 20.0,
                "percent_available": 100.0,
                "percent_not_available": 0.0,
                "mean": 2.5,
            },
        )
        self.assertDictEqual(
            generate_mean_stats("AA", self.df.groupby("location")),
            {
                "type": "mean",
                "locations": {
                    "A": {
                        "mean": 1.0,
                        "reported": 1,
                        "available": 1,
                        "missing": 0,
                        "not_available": 0,
                        "percent_reported": 100.0,
                        "percent_missing": 0.0,
                        "percent_not_available": 0.0,
                        "percent_available": 100.0,
                    },
                    "B": {
                        "mean": 2.5,
                        "reported": 2,
                        "available": 2,
                        "missing": 0,
                        "not_available": 0,
                        "percent_reported": 100.0,
                        "percent_available": 100.0,
                        "percent_not_available": 0.0,
                        "percent_missing": 0.0,
                    },
                    "C": {
                        "mean": 4.0,
                        "reported": 1,
                        "available": 1,
                        "not_available": 0,
                        "missing": 0,
                        "percent_reported": 100.0,
                        "percent_available": 100.0,
                        "percent_not_available": 0.0,
                        "percent_missing": 0.0,
                    },
                    "D": {
                        "mean": 0.0,
                        "reported": 0,
                        "not_available": 0,
                        "available": 0,
                        "missing": 1,
                        "percent_reported": 0.0,
                        "percent_available": 0.0,
                        "percent_not_available": 0.0,
                        "percent_missing": 100.0,
                    },
                },
            },
        )

    def test_generate_mean_stats_na(self):
        self.assertDictEqual(
            generate_mean_stats("AA", self.df, null_value=4),
            {
                "type": "mean",
                "reported": 4,
                "available": 3,
                "not_available": 1,
                "missing": 1,
                "percent_reported": 80.0,
                "percent_missing": 20.0,
                "percent_available": 75.0,
                "percent_not_available": 25.0,
                "mean": 2.0,
            },
        )
        self.assertDictEqual(
            generate_mean_stats("AA", self.df.groupby("location"), null_value=4),
            {
                "type": "mean",
                "locations": {
                    "A": {
                        "mean": 1.0,
                        "reported": 1,
                        "available": 1,
                        "missing": 0,
                        "not_available": 0,
                        "percent_reported": 100.0,
                        "percent_missing": 0.0,
                        "percent_not_available": 0.0,
                        "percent_available": 100.0,
                    },
                    "B": {
                        "mean": 2.5,
                        "reported": 2,
                        "available": 2,
                        "missing": 0,
                        "not_available": 0,
                        "percent_reported": 100.0,
                        "percent_available": 100.0,
                        "percent_not_available": 0.0,
                        "percent_missing": 0.0,
                    },
                    "C": {
                        "mean": 0.0,
                        "reported": 1,
                        "available": 0,
                        "not_available": 1,
                        "missing": 0,
                        "percent_reported": 100.0,
                        "percent_available": 0.0,
                        "percent_not_available": 100.0,
                        "percent_missing": 0.0,
                    },
                    "D": {
                        "mean": 0.0,
                        "reported": 0,
                        "not_available": 0,
                        "available": 0,
                        "missing": 1,
                        "percent_reported": 0.0,
                        "percent_available": 0.0,
                        "percent_not_available": 0.0,
                        "percent_missing": 100.0,
                    },
                },
            },
        )

    def test_generate_histogram_stats(self):
        self.assertDictEqual(
            generate_histogram_stats("AB", self.df, [2, 3, 4, 5, 6]),
            {
                "type": "histogram",
                "labels": None,
                "meta": [(2, 2), (3, 3), (4, 4), (5, 5), (6, 6)],
                "histogram": {
                    2: (1, 20.0),
                    3: (1, 20.0),
                    4: (1, 20.0),
                    5: (1, 20.0),
                    6: (1, 20.0),
                },
                "reported": 5,
                "available": 5,
                "not_available": 0,
                "missing": 0,
                "percent_reported": 100.0,
                "percent_available": 100.0,
                "percent_missing": 0.0,
                "percent_not_available": 0.0,
                "total": 5,
            },
        )
        self.assertDictEqual(
            generate_histogram_stats(
                "AB", self.df.groupby("location"), [2, 3, 4, 5, 6]
            ),
            {
                "type": "histogram",
                "labels": None,
                "meta": [(2, 2), (3, 3), (4, 4), (5, 5), (6, 6)],
                "locations": {
                    "A": {
                        "missing": 0,
                        "not_available": 0,
                        "reported": 1,
                        "available": 1,
                        "total": 1,
                        "percent_reported": 100.0,
                        "percent_available": 100.0,
                        "percent_missing": 0.0,
                        "percent_not_available": 0.0,
                        "histogram": {
                            2: (1, 100.0),
                            3: (0, 0.0),
                            4: (0, 0.0),
                            5: (0, 0.0),
                            6: (0, 0.0),
                        },
                    },
                    "B": {
                        "missing": 0,
                        "not_available": 0,
                        "reported": 2,
                        "available": 2,
                        "total": 2,
                        "percent_reported": 100.0,
                        "percent_available": 100.0,
                        "percent_not_available": 0.0,
                        "percent_missing": 0.0,
                        "histogram": {
                            2: (0, 0.0),
                            3: (1, 50.0),
                            4: (1, 50.0),
                            5: (0, 0.0),
                            6: (0, 0.0),
                        },
                    },
                    "C": {
                        "missing": 0,
                        "not_available": 0,
                        "reported": 1,
                        "available": 1,
                        "total": 1,
                        "percent_reported": 100.0,
                        "percent_available": 100.0,
                        "percent_missing": 0.0,
                        "percent_not_available": 0.0,
                        "histogram": {
                            2: (0, 0.0),
                            3: (0, 0.0),
                            4: (0, 0.0),
                            5: (1, 100.0),
                            6: (0, 0.0),
                        },
                    },
                    "D": {
                        "missing": 0,
                        "not_available": 0,
                        "reported": 1,
                        "available": 1,
                        "total": 1,
                        "percent_reported": 100.0,
                        "percent_available": 100.0,
                        "percent_missing": 0.0,
                        "percent_not_available": 0.0,
                        "histogram": {
                            2: (0, 0.0),
                            3: (0, 0.0),
                            4: (0, 0.0),
                            5: (0, 0.0),
                            6: (1, 100.0),
                        },
                    },
                },
            },
        )

    def test_generate_histogram_stats_na(self):
        self.assertDictEqual(
            generate_histogram_stats(
                "AB", self.df, [2, 3, 4, 5, 6], null_value=4
            ),
            {
                "type": "histogram",
                "labels": None,
                "meta": [(2, 2), (3, 3), (5, 5), (6, 6)],
                "histogram": {
                    2: (1, 25.0),
                    3: (1, 25.0),
                    5: (1, 25.0),
                    6: (1, 25.0),
                },
                "reported": 5,
                "available": 4,
                "not_available": 1,
                "missing": 0,
                "percent_reported": 100.0,
                "percent_available": 80.0,
                "percent_missing": 0.0,
                "percent_not_available": 20.0,
                "total": 5,
            },
        )
        self.assertDictEqual(
            generate_histogram_stats(
                "AB", self.df.groupby("location"), [2, 3, 4, 5, 6], null_value=6
            ),
            {
                "type": "histogram",
                "labels": None,
                "meta": [(2, 2), (3, 3), (4, 4), (5, 5)],
                "locations": {
                    "A": {
                        "missing": 0,
                        "not_available": 0,
                        "reported": 1,
                        "available": 1,
                        "total": 1,
                        "percent_reported": 100.0,
                        "percent_available": 100.0,
                        "percent_missing": 0.0,
                        "percent_not_available": 0.0,
                        "histogram": {
                            2: (1, 100.0),
                            3: (0, 0.0),
                            4: (0, 0.0),
                            5: (0, 0.0),
                        },
                    },
                    "B": {
                        "missing": 0,
                        "not_available": 0,
                        "reported": 2,
                        "available": 2,
                        "total": 2,
                        "percent_reported": 100.0,
                        "percent_available": 100.0,
                        "percent_not_available": 0.0,
                        "percent_missing": 0.0,
                        "histogram": {
                            2: (0, 0.0),
                            3: (1, 50.0),
                            4: (1, 50.0),
                            5: (0, 0.0),
                        },
                    },
                    "C": {
                        "missing": 0,
                        "not_available": 0,
                        "reported": 1,
                        "available": 1,
                        "total": 1,
                        "percent_reported": 100.0,
                        "percent_available": 100.0,
                        "percent_missing": 0.0,
                        "percent_not_available": 0.0,
                        "histogram": {
                            2: (0, 0.0),
                            3: (0, 0.0),
                            4: (0, 0.0),
                            5: (1, 100.0),
                        },
                    },
                    "D": {
                        "missing": 0,
                        "not_available": 1,
                        "reported": 1,
                        "available": 0,
                        "total": 1,
                        "percent_reported": 100.0,
                        "percent_available": 0.0,
                        "percent_missing": 0.0,
                        "percent_not_available": 100.0,
                        "histogram": {
                            2: (0, 0.0),
                            3: (0, 0.0),
                            4: (0, 0.0),
                            5: (0, 0.0),
                        },
                    },
                },
            },
        )

    def test_generate_multiselect_histogram_stats(self):
        opt = [1, 2, 3, 4, 5, 6]
        self.assertDictEqual(
            generate_multiselect_histogram_stats("AC", self.df, opt),
            {
                "type": "histogram",
                "histogram": {
                    1: (1, 20.0),
                    2: (3, 60.0),
                    3: (2, 40.0),
                    4: (1, 20.0),
                    5: (1, 20.0),
                    6: (1, 20.0),
                },
                "reported": 5,
                "missing": 0,
                "percent_reported": 100.0,
                "percent_missing": 0.0,
                "labels": None,
                "meta": [],
            },
        )
        self.assertDictEqual(
            generate_multiselect_histogram_stats(
                "AC", self.df.groupby("location"), opt
            ),
            {
                "type": "histogram",
                "labels": None,
                "meta": [],
                "locations": {
                    "A": {
                        "missing": 0,
                        "reported": 1,
                        "percent_reported": 100.0,
                        "percent_missing": 0.0,
                        "histogram": {
                            1: (1, 100.0),
                            2: (1, 100.0),
                            3: (0, 0.0),
                            4: (0, 0.0),
                            5: (0, 0.0),
                            6: (0, 0.0),
                        },
                    },
                    "B": {
                        "missing": 0,
                        "reported": 2,
                        "percent_reported": 100.0,
                        "percent_missing": 0.0,
                        "histogram": {
                            1: (0, 0.0),
                            2: (2, 100.0),
                            3: (1, 50.0),
                            4: (1, 50.0),
                            5: (0, 0.0),
                            6: (0, 0.0),
                        },
                    },
                    "C": {
                        "missing": 0,
                        "reported": 1,
                        "percent_reported": 100.0,
                        "percent_missing": 0.0,
                        "histogram": {
                            1: (0, 0.0),
                            2: (0, 0.0),
                            3: (1, 100.0),
                            4: (0, 0.0),
                            5: (0, 0.0),
                            6: (0, 0.0),
                        },
                    },
                    "D": {
                        "missing": 0,
                        "reported": 1,
                        "percent_reported": 100.0,
                        "percent_missing": 0.0,
                        "histogram": {
                            1: (0, 0.0),
                            2: (0, 0.0),
                            3: (0, 0.0),
                            4: (0, 0.0),
                            5: (1, 100.0),
                            6: (1, 100.0),
                        },
                    },
                },
            },
        )

    def test_generate_count_stats(self):
        self.assertDictEqual(
            generate_count_stats("AA", self.df),
            {
                "type": "count",
                "reported": 4,
                "available": 4,
                "missing": 1,
                "not_available": 0,
                "percent_reported": 80.0,
                "percent_missing": 20.0,
                "percent_not_available": 0.0,
                "percent_available": 100.0,
                "total": 5,
            },
        )
        self.assertDictEqual(
            generate_count_stats("AA", self.df.groupby("location")),
            {
                "type": "count",
                "locations": {
                    "A": {
                        "missing": 0,
                        "reported": 1,
                        "available": 1,
                        "not_available": 0,
                        "total": 1,
                        "percent_reported": 100.0,
                        "percent_missing": 0.0,
                        "percent_not_available": 0.0,
                        "percent_available": 100.0,
                    },
                    "B": {
                        "missing": 0,
                        "not_available": 0,
                        "reported": 2,
                        "available": 2,
                        "total": 2,
                        "percent_reported": 100.0,
                        "percent_missing": 0.0,
                        "percent_not_available": 0.0,
                        "percent_available": 100.0,
                    },
                    "C": {
                        "missing": 0,
                        "not_available": 0,
                        "reported": 1,
                        "available": 1,
                        "total": 1,
                        "percent_reported": 100.0,
                        "percent_missing": 0.0,
                        "percent_not_available": 0.0,
                        "percent_available": 100.0,
                    },
                    "D": {
                        "missing": 1,
                        "reported": 0,
                        "available": 0,
                        "not_available": 0,
                        "total": 1,
                        "percent_reported": 0.0,
                        "percent_missing": 100.0,
                        "percent_available": 0.0,
                        "percent_not_available": 0.0,
                    },
                },
            },
        )

    def test_generate_count_stats_na(self):
        self.assertDictEqual(
            generate_count_stats("AA", self.df, null_value=4),
            {
                "type": "count",
                "reported": 4,
                "available": 3,
                "missing": 1,
                "not_available": 1,
                "percent_reported": 80.0,
                "percent_missing": 20.0,
                "percent_not_available": 25.0,
                "percent_available": 75.0,
                "total": 5,
            },
        )
        self.assertDictEqual(
            generate_count_stats(
                "AA", self.df.groupby("location"), null_value=3
            ),
            {
                "type": "count",
                "locations": {
                    "A": {
                        "missing": 0,
                        "reported": 1,
                        "available": 1,
                        "not_available": 0,
                        "total": 1,
                        "percent_reported": 100.0,
                        "percent_missing": 0.0,
                        "percent_not_available": 0.0,
                        "percent_available": 100.0,
                    },
                    "B": {
                        "missing": 0,
                        "not_available": 1,
                        "reported": 2,
                        "available": 1,
                        "total": 2,
                        "percent_reported": 100.0,
                        "percent_missing": 0.0,
                        "percent_not_available": 50.0,
                        "percent_available": 50.0,
                    },
                    "C": {
                        "missing": 0,
                        "not_available": 0,
                        "reported": 1,
                        "available": 1,
                        "total": 1,
                        "percent_reported": 100.0,
                        "percent_missing": 0.0,
                        "percent_not_available": 0.0,
                        "percent_available": 100.0,
                    },
                    "D": {
                        "missing": 1,
                        "reported": 0,
                        "available": 0,
                        "not_available": 0,
                        "total": 1,
                        "percent_reported": 0.0,
                        "percent_missing": 100.0,
                        "percent_available": 0.0,
                        "percent_not_available": 0.0,
                    },
                },
            },
        )

    def test_percent_of(self):
        self.assertEqual(percent_of(2, 10), 20.0)
        self.assertEqual(percent_of(3, 0), 0)

    def test_generate_field_stats(self):
        self.assertDictEqual(
            generate_field_stats(
                {"type": "integer", "tag": "AA", "analysis_type": "count"},
                self.df,
            ),
            {
                "type": "count",
                "reported": 4,
                "available": 4,
                "not_available": 0,
                "missing": 1,
                "percent_reported": 80.0,
                "percent_missing": 20.0,
                "percent_available": 100.0,
                "percent_not_available": 0.0,
                "total": 5,
            },
        )
