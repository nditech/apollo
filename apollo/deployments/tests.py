# -*- coding: utf-8 -*-
from datetime import datetime, timezone
import pathlib
from unittest import mock

from flask_testing import TestCase

from apollo import services
from apollo.core import db
from apollo.testutils import factory as test_factory, fixtures

DEFAULT_FIXTURES_PATH = pathlib.Path(__file__).parent / 'fixtures'


class EventServiceTest(TestCase):
    def create_app(self):
        return test_factory.create_test_app()

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.close()
        db.drop_all()

    def test_overlapping_events(self):
        fixtures_path = DEFAULT_FIXTURES_PATH / '17720ddbe13.sql'
        fixtures.load_sql_fixture(fixtures_path)

        ##############################################################
        #
        #   start and end times:
        #
        #   event 1: 2005-12-13 01:00:00+01 - 2005-12-14 00:59:59+01
        #   event 2: 2005-12-14 01:00:00+01 - 2005-12-15 00:59:59+01
        #   event 3: 2005-12-14 01:00:00+01 - 2005-12-16 00:59:59+01
        #
        ##############################################################

        event1, event2, event3 = services.events.find().order_by('id').all()

        # the 'no-overlap' case
        with mock.patch.object(
                services.events, 'default', return_value=event1):
            event = services.events.default()
            events = services.events.overlapping_events(event).all()

            self.assertIn(event, events)
            self.assertEqual(len(events), 1)

        # the overlap cases:
        # 1 - at a time they do overlap
        with mock.patch.object(
                services.events, 'default', return_value=event2):
            event = services.events.default()
            timestamp = datetime(2005, 12, 14, 16, tzinfo=timezone.utc)
            events = services.events.overlapping_events(event, timestamp).all()

            self.assertIn(event2, events)
            self.assertIn(event3, events)
            self.assertNotIn(event1, events)
            self.assertEqual(len(events), 2)

        # 2 - at a time they do not overlap
        with mock.patch.object(
                services.events, 'default', return_value=event3):
            event = services.events.default()
            timestamp = datetime(2005, 12, 16, 2, tzinfo=timezone.utc)
            events = services.events.overlapping_events(event, timestamp).all()

            self.assertIn(event3, events)
            self.assertNotIn(event1, events)
            self.assertNotIn(event2, events)
            self.assertEqual(len(events), 1)
