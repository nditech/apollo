# -*- coding: utf-8 -*-
import pathlib
from datetime import datetime, timezone
from unittest import mock

from apollo import services
from apollo.testutils import fixtures

DEFAULT_FIXTURES_PATH = pathlib.Path(__file__).parent / "fixtures"


def test_overlapping_events(app):
    """Tests overlapping events."""
    fixtures_path = DEFAULT_FIXTURES_PATH / "17720ddbe13.sql"
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

    event1, event2, event3 = services.events.find().order_by("id").all()

    # the 'no-overlap' case
    with mock.patch.object(services.events, "default", return_value=event1):
        event = services.events.default()
        events = services.events.overlapping_events(event).all()

        assert event in events
        assert len(events) == 1

    # the overlap cases:
    # 1 - at a time they do overlap
    with mock.patch.object(services.events, "default", return_value=event2):
        event = services.events.default()
        timestamp = datetime(2005, 12, 14, 16, tzinfo=timezone.utc)
        events = services.events.overlapping_events(event, timestamp).all()

        assert event2 in events
        assert event3 in events
        assert event1 not in events
        assert len(events) == 2

    # 2 - at a time they do not overlap
    with mock.patch.object(services.events, "default", return_value=event3):
        event = services.events.default()
        timestamp = datetime(2005, 12, 16, 2, tzinfo=timezone.utc)
        events = services.events.overlapping_events(event, timestamp).all()

        assert event3 in events
        assert event1 not in events
        assert event2 not in events
        assert len(events) == 1
