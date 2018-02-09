# -*- coding: utf-8 -*-
from datetime import datetime

import pytz
from sqlalchemy import and_, or_

from apollo import settings
from apollo.dal.service import Service
from apollo.deployments.rmodels import (
    Event, FormSet, LocationSet, ParticipantSet)
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
            Event.start <= upper_bound, Event.start >= lower_bound
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
        now = current_timestamp().astimezone(app_time_zone)

        lower_bound = app_time_zone.localize(
                datetime.combine(now, datetime.min.time())
        ).astimezone(pytz.utc)
        upper_bound = app_time_zone.localize(
                datetime.combine(now, datetime.max.time())
        ).astimezone(pytz.utc)

        # events starting after the specified event starts, and before it ends
        expr1 = and_(Event.start >= event.start, Event.start <= event.end)

        # events ending after the specified event starts, and ending before it
        expr2 = and_(Event.end >= event.start, Event.end <= event.end)

        # events starting before the event starts, and ending after it does
        expr3 = and_(Event.end >= event.start, Event.end >= event.end)

        overlapping = self.filter(
            or_(expr1, expr2, expr3),
            Event.start <= upper_bound, Event.end >= lower_bound).all()

        return overlapping if overlapping else [event]


class FormSetService(Service):
    __model__ = FormSet


class LocationSetService(Service):
    __model__ = LocationSet


class ParticipantSetService(Service):
    __model__ = ParticipantSet
