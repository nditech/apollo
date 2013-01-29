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
# from .importer import _save_location_type


class ImporterTest(TestCase):
    location_type_data = None
    location_data = None
    observer_data = None

    def setUp(self):
        root = logging.getLogger('south')
        root.setLevel(logging.INFO)

        self.location_type_data = Dataset(headers=['Type', 'Parent'])
        self.location_type_data.append(['Country', ''])
        self.location_type_data.append(['Zone', 'Country'])
        self.location_type_data.append(['State', 'Zone'])
        self.location_type_data.append(['Ward', 'State'])
        self.location_type_data.append(['LGA', 'Ward'])
        self.location_type_data.append(['Polling Unit', 'LGA'])
        # sanity check
        self.location_type_data.append(['Continent', 'Fake'])

        self.location_data = Dataset(headers=['Name', 'Code', 'Parent', 'Location Type'])
        self.location_data.append(['Nigeria', 'NG', '', 'Country'])
        self.location_data.append(['South-West', 'SW', 'Nigeria', 'Zone'])
        self.location_data.append(['Lagos', 'LAG', 'South-West', 'State'])
        self.location_data.append(['Lagos Central', 'LGC', 'Lagos', 'Ward'])
        self.location_data.append(['Ikeja', 'IKJ', 'Lagos Central', 'LGA'])
        self.location_data.append(['Alade Market', 'ALM', 'Ikeja', 'Polling Unit'])
        
        # sanity checks
        self.location_data.append(['Antarctica', 'ANTA', '', 'Continent'])
        self.location_data.append(['California', 'CA', 'USA', 'State'])

        self.observer_data = Dataset(headers=['Observer ID', 'Name', 'Phone 1',
                                    'Phone 2', 'Phone 3', 'Role', 'Location',
                                    'Location Type', 'Supervisor ID', 'Gender',
                                    'Partner'])
        self.observer_data.append(['1001', 'John Doe', '01234', '', '', 'Supervisor',
            'Alade Market', 'Polling Unit', '', '', 'NDI'])
        self.observer_data.append(['1002', 'Joe Blow', '56789', '', '', 'Monitor',
            'Alade Market', 'Polling Unit', '', '', 'NDI'])
        self.observer_data.append(['1002', 'Jane Plain', '56789', '', '', 'Monitor',
            'Alade Market', 'Polling Unit', '', '', 'Carrot'])
        self.observer_data.append(['1002', 'Jane Plain', '56789', '', '', 'Monitor',
            'Antarctica', 'Polling Unit', '', '', 'Carrot'])

    def test_all_imports(self):
        # import location types
        with TemporaryFile() as t1:
            t1.write(self.location_type_data.csv)
            t1.seek(0)
            errors1 = import_csv_location_types(t1)

        with TemporaryFile() as t2:
            t2.write(self.location_data.csv)
            t2.seek(0)
            errors2 = import_csv_locations(t2)

        with TemporaryFile() as t3:
            t3.write(self.observer_data.csv)
            t3.seek(0)
            errors3 = import_csv_contacts(t3)

        self.assertEqual(len(errors1), 1)
        self.assertEqual(LocationType.objects.count(), 6)

        self.assertEqual(len(errors2), 2)
        self.assertEqual(Location.objects.count(), 6)

        l1 = Location.objects.get(name='Nigeria')
        l2 = Location.objects.get(name='Alade Market')

        self.assertTrue(l2 in l1.get_descendants())

        self.assertEqual(Observer.objects.count(), 2)

        self.assertEqual(len(errors3), 1)

        partner = Partner.objects.get(name='NDI')

        self.assertEqual(partner.observer_set.count(), 1)
