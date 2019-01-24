# -*- coding: utf-8 -*-
from datetime import datetime

import pytz
from sqlalchemy import and_, or_

from apollo import settings
from apollo.dal.service import Service
from apollo.deployments.models import Event
from apollo.utils import current_timestamp

app_time_zone = pytz.timezone(settings.TIMEZONE)


class EventService(Service):
    __model__ = Event

    def default(self):
        now = current_timestamp().astimezone(app_time_zone)

        lower_bound = datetime.combine(now, datetime.min.time())
        upper_bound = datetime.combine(now, datetime.max.time())

        # convert back to UTC because datetime.combine() returns
        # naive objects
        lower_bound = app_time_zone.localize(lower_bound).astimezone(pytz.utc)
        upper_bound = app_time_zone.localize(upper_bound).astimezone(pytz.utc)

        event = self.filter(
            Event.start <= upper_bound, Event.end >= lower_bound
        ).order_by(Event.start.desc()).first()

        if event:
            return event

        # if there's no event, pick the closest past event
        event = self.filter(Event.end <= lower_bound).order_by(
            Event.end.desc()).first()

        if event:
            return event

        # if there's no event, pick the closest future event
        event = self.filter(Event.start >= upper_bound).order_by(
            Event.start).first()

        if event:
            return event

        return None

    def overlapping_events(self, event):
        # case 1: all events completely contained within the timespan
        # of the passed-in event
        expr1 = and_(Event.start >= event.start, Event.end <= event.end)

        # case 2: all events that start before the passed-in event,
        # and end before it ends
        expr2 = and_(Event.start <= event.start, Event.end >= event.start)

        # case 3: all events that start during the passed-in event,
        # and end after it
        expr3 = and_(Event.start <= event.end, Event.end >= event.end)

        overlapping = self.filter(
            Event.deployment_id == event.deployment_id,
            or_(expr1, expr2, expr3))

        if overlapping.with_entities(Event.id).count() > 0:
            return overlapping

        return self.query.filter_by(id=event.id)
