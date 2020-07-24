# -*- coding: utf-8 -*-
from sqlalchemy import and_, or_

from apollo.dal.service import Service
from apollo.deployments.models import Event
from apollo.utils import current_timestamp


class EventService(Service):
    __model__ = Event

    def default(self):
        now = current_timestamp()

        event = self.filter(
            Event.start <= now, Event.end >= now
        ).order_by(Event.start.desc(), Event.id).first()

        if event:
            return event

        # if there's no event, pick the closest past event
        event = self.filter(Event.end <= now).order_by(
            Event.end.desc(), Event.id).first()

        if event:
            return event

        # if there's no event, pick the closest future event
        event = self.filter(Event.start >= now).order_by(
            Event.start, Event.id).first()

        if event:
            return event

        return None

    def overlapping_events(self, event, timestamp=None):
        return self.__model__.overlapping_events(event, timestamp=timestamp)
