from apollo import settings
from apollo.core import Service
from apollo.deployments.models import Event
from datetime import datetime
from flask.ext.principal import Permission, ItemNeed, RoleNeed
from flask.ext.security import current_user
from mongoengine import Q
import pytz

app_time_zone = pytz.timezone(settings.TIMEZONE)
utc_time_zone = pytz.utc


class EventsService(Service):
    __model__ = Event

    def find(self, **kwargs):
        _kwargs = self._set_default_filter_parameters({})

        if current_user.is_authenticated():
            kwargs['pk__in'] = [event.pk for event in filter(
                    lambda f: Permission(ItemNeed('access_event', f, 'object'),
                                         RoleNeed('admin')).can(),
                    self.__model__.objects.filter(**_kwargs))]

        return super(EventsService, self).find(**kwargs)

    def default(self):
        now = utc_time_zone.localize(datetime.utcnow()).astimezone(app_time_zone)

        lower_bound = datetime.combine(now, datetime.min.time())
        upper_bound = datetime.combine(now, datetime.max.time())

        # convert lower_bound and upper_bound to GMT
        lower_bound = app_time_zone.localize(lower_bound).astimezone(utc_time_zone)
        upper_bound = app_time_zone.localize(upper_bound).astimezone(utc_time_zone)

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

        # if no event was created, create a default one
        return self.get_or_create(name='Default')

    def overlapping_events(self, event):
        now = utc_time_zone.localize(datetime.utcnow()).astimezone(app_time_zone)

        lower_bound = app_time_zone.localize(
                datetime.combine(now, datetime.min.time())).astimezone(utc_time_zone)
        upper_bound = app_time_zone.localize(
                datetime.combine(now, datetime.max.time())).astimezone(utc_time_zone)

        return self.find().filter(
            Q(start_date__gte=event.start_date, start_date__lte=event.end_date)
            | Q(end_date__gte=event.start_date, end_date__lte=event.end_date)
            | Q(start_date__lte=event.start_date, end_date__gte=event.end_date)
        ).filter(start_date__lte=upper_bound, end_date__gte=lower_bound)
