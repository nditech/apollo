from __future__ import unicode_literals
from core.documents import Event, LocationType
from core.tests import BaseTestCase


class LocationsTest(BaseTestCase):
    fixtures = 'model_tests.json'

    def test_root(self):
        event = Event.objects.get(name='default')
        root = LocationType.get_root_for_event(event)
        r2 = LocationType.objects.get(name='Country')
        self.assertEqual(root, r2)

    def test_children(self):
        # Country > Zone > State > Senatorial District > LGA
        root = LocationType.objects.get(name='Country')
        lga = LocationType.objects.get(name='LGA')
        zone = LocationType.objects.get(name='Zone')

        self.assertIn(zone, root.get_children())
        self.assertNotIn(lga, root.get_children())
