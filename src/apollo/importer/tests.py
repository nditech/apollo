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
from .importer import *


class ImporterTest(TestCase):
    def setUp(self):
        root = logging.getLogger('south')
        root.setLevel(logging.INFO)

    def test_excel_location_type_import(self):
        data = Dataset(headers=['Type', 'Parent'])
        data.append(['Root', ''])
        data.append(['Branch1', 'Root'])
        data.append(['Branch2', 'Branch1'])
        data.append(['Continent', 'Fake'])  # for sanity check

        with TemporaryFile() as temp:
            temp.write(data.xls)

            # reset stream pointer for reading
            temp.seek(0)

            errors = import_excel_location_types(temp)
            logging.info(errors)

            self.assertEqual(len(errors), 1)
            self.assertEqual(len(LocationType.objects.all()), 3)

    def test_csv_location_type_import(self):
        data = Dataset(headers=['Type', 'Parent'])
        data.append(['Country', ''])
        data.append(['Region', 'Country'])
        data.append(['State', 'Region'])
        data.append(['Continent', 'Fake'])  # for sanity check

        with TemporaryFile() as temp:
            temp.write(data.csv)

            # reset stream pointer for reading
            temp.seek(0)

            errors = import_csv_location_types(temp)
            logging.info(errors)

            self.assertEqual(len(errors), 1)
            self.assertEqual(len(LocationType.objects.all()), 3)
