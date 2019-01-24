# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, timezone
from unittest import mock

from flask_testing import TestCase

from apollo import services
from apollo.core import db
from apollo.testutils import factory as test_factory, fixtures


class EventServiceTest(TestCase):
    def create_app(self):
        return test_factory.create_test_app()

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.close()
        db.drop_all()

    def test_active_form_selector(self):
        event1_start = datetime(2005, 12, 13, tzinfo=timezone.utc)
        event1_end = event1_start + timedelta(days=1, seconds=-1)

        event2_start = datetime(2005, 12, 14, tzinfo=timezone.utc)
        event2_end = event2_start + timedelta(days=1, seconds=-1)

        event3_start = datetime(2005, 12, 14, tzinfo=timezone.utc)
        event3_end = event3_start + timedelta(days=2, seconds=-1)

        deployment = fixtures.create_deployment('Demo')

        event1 = fixtures.create_event(
            deployment.id, 'Event 1', event1_start, event1_end)
        event2 = fixtures.create_event(
            deployment.id, 'Event 2', event2_start, event2_end)
        event3 = fixtures.create_event(
            deployment.id, 'Event 3', event3_start, event3_end)

        with mock.patch.object(
                services.events, 'default', return_value=event1):
            event = services.events.default()
            events = services.events.overlapping_events(event).all()

            self.assertIn(event, events)
            self.assertEqual(len(events), 1)

        with mock.patch.object(
                services.events, 'default', return_value=event2):
            event = services.events.default()
            events = services.events.overlapping_events(event).all()

            self.assertIn(event2, events)
            self.assertIn(event3, events)
            self.assertNotIn(event1, events)
            self.assertEqual(len(events), 2)

        with mock.patch.object(
                services.events, 'default', return_value=event3):
            event = services.events.default()
            events = services.events.overlapping_events(event).all()

            self.assertIn(event2, events)
            self.assertIn(event3, events)
            self.assertNotIn(event1, events)
            self.assertEqual(len(events), 2)
