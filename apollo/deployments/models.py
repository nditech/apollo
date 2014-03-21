from ..core import db


# Deployment
class Deployment(db.Document):
    name = db.StringField(required=True)
    hostnames = db.ListField(db.StringField())

    meta = {
        'indexes': [
            ['hostnames']
        ]
    }

    def __unicode__(self):
        return self.name


# Event
class Event(db.Document):
    name = db.StringField()
    start_date = db.DateTimeField()
    end_date = db.DateTimeField()

    deployment = db.ReferenceField(Deployment)

    meta = {
        'indexes': [
            ['deployment', 'name'],
            ['deployment', 'start_date', '-end_date']
        ]
    }

    @classmethod
    def default(cls):
        current_timestamp = datetime.utcnow()
        ct = datetime(
            year=current_timestamp.year,
            month=current_timestamp.month,
            day=current_timestamp.day
        )

        lower_bound = ct - timedelta(hours=23)
        upper_bound = ct + timedelta(hours=23)

        event = cls.objects(
            start_date__lte=lower_bound, end_date__gte=upper_bound
        ).order_by('-start_date').first()
        if event:
            return event

        event = cls.objects(
            end_date__lte=lower_bound
        ).order_by('-end_date').first()
        if event:
            return event

        event = cls.objects(
            start_date__gte=upper_bound
        ).order_by('start_date').first()
        if event:
            return event
        return None

    def __unicode__(self):
        return self.name
