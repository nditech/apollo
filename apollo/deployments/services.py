# -*- coding: utf-8 -*-
from apollo.dal.service import Service
from apollo.deployments.models import Event


class EventService(Service):
    __model__ = Event

    def default(self):
        return self.__model__.default()

    def overlapping_events(self, event, timestamp=None):
        return self.__model__.overlapping_events(event, timestamp)
