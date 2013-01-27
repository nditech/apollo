"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import logging
from tempfile import TemporaryFile
from django.test import TestCase
from tablib import Dataset
from core.models import *
from .importer import _save_location_type


class ImporterTest(TestCase):
    location_type_data = None
    location_data = None
    observer_data = None

    def setUp(self):
        root = logging.getLogger('south')
        root.setLevel(logging.INFO)

        self.location_type_data = Dataset(headers=['Type', 'Parent'])
        self.location_type_data.append(['Country', ''])
        self.location_type_data.append(['Region', 'Country'])
        self.location_type_data.append(['State', 'Region'])
        # sanity check
        self.location_type_data.append(['Continent', 'Fake'])

        self.location_data = Dataset(headers=['Name', 'Code', 'Location Type'])
        self.location_data.append(['Lagos', 'LAG', 'State'])
        self.location_data.append(['South-West', 'SW', 'Region'])
        # sanity check
        self.location_data.append(['Antarctica', 'ANTA', 'Continent'])

    # def test_excel_location_type_import(self):
    #     with TemporaryFile() as temp:
    #         temp.write(self.location_type_data.xls)

    #         # reset stream pointer for reading
    #         temp.seek(0)

    #         errors = import_excel_location_types(temp)
    #         logging.info(errors)

    #         self.assertEqual(len(errors), 1)
    #         self.assertEqual(LocationType.objects.count(), 3)

    # def test_csv_location_type_import(self):
    #     with TemporaryFile() as temp:
    #         temp.write(self.location_type_data.csv)

    #         # reset stream pointer for reading
    #         temp.seek(0)

    #         errors = import_csv_location_types(temp)
    #         logging.info(errors)

    #         self.assertEqual(len(errors), 1)
    #         self.assertEqual(LocationType.objects.count(), 3)

    # def test_csv_location_import(self):
    #     with TemporaryFile() as temp1:
    #         temp1.write(self.location_type_data.csv)
    #         temp1.seek(0)

    #         import_csv_location_types(temp1)

    #     with TemporaryFile() as temp2:
    #         temp2.write(self.location_data.csv)
    #         temp2.seek(0)

    #         errors = import_csv_locations(temp2)

    #         self.assertEqual(len(errors), 1)
    #         self.assertEqual(Location.objects.count(), 2)

    # def test_excel_location_import(self):
    #     with TemporaryFile() as temp1:
    #         temp1.write(self.location_type_data.xls)
    #         temp1.seek(0)

    #         import_excel_location_types(temp1)

    #     with TemporaryFile() as temp2:
    #         temp2.write(self.location_data.xls)
    #         temp2.seek(0)

    #         errors = import_excel_locations(temp2)

    #         self.assertEqual(len(errors), 1)
    #         self.assertEqual(Location.objects.count(), 2)

    def test1(self):
        _save_location_type('Country', '')
        _save_location_type('Zone', 'Country')
        _save_location_type('State', 'Zone')
        _save_location_type('LGA', 'State')
        _save_location_type('Ward', 'LGA')
        _save_location_type('PU', 'Ward')

        self.assertEqual(LocationType.objects.count(), 6)

    def test2(self):
        _save_location_type('Country', '')
        _save_location_type('Region', 'Country')

        self.assertEqual(LocationType.objects.count(), 2)
