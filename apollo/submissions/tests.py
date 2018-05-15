import numpy as np
import pandas as pd
from unittest import TestCase
from apollo.submissions.incidents import incidents_csv


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
