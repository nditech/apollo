from ..core import Service
from .models import Event
from datetime import datetime, timedelta


class EventsService(Service):
    __model__ = Event

    def default(self):
        current_timestamp = datetime.utcnow()
        current_date = datetime(
            year=current_timestamp.year,
            month=current_timestamp.month,
            day=current_timestamp.day
        )

        lower_bound = current_date - timedelta(hours=23)
        upper_bound = current_date + timedelta(hours=23)

        event = self.find(start_date__lte=lower_bound,
                          end_date__gte=upper_bound) \
            .order_by('-start_date').first()

        if event:
            return event

        event = self.find(end_date__lte=lower_bound) \
            .order_by('-end_date').first()

        if event:
            return event

        event = self.find(start_date__gte=upper_bound) \
            .order_by('start_date').first()

        if event:
            return event
