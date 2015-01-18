from ..core import Service
from .models import Event
from datetime import datetime
from mongoengine import Q


class EventsService(Service):
    __model__ = Event

    def default(self):
        now = datetime.utcnow()

        lower_bound = datetime.combine(now, datetime.min.time())
        upper_bound = datetime.combine(now, datetime.max.time())

        event = self.find(start_date__lte=upper_bound,
                          end_date__gte=lower_bound) \
            .order_by('-start_date').first()

        if event:
            return event

        # choose the past event that's closest the current date
        event = self.find(end_date__lte=lower_bound) \
            .order_by('-end_date').first()

        if event:
            return event

        # if the previous fails, then choose the future event closes
        event = self.find(start_date__gte=upper_bound) \
            .order_by('start_date').first()

        if event:
            return event

    def overlapping_events(self, event):
        return self.find().filter(
            Q(start_date__gte=event.start_date, start_date__lte=event.end_date)
            | Q(end_date__gte=event.start_date, end_date__lte=event.end_date)
        )
