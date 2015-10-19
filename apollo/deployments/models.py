from apollo.core import db
from datetime import datetime
from functools import partial


class ParticipantPropertyName(db.StringField):
    def validate(self, value):
        from ..participants.models import Participant
        if value in Participant._fields.keys():
            self.error(
                'String value cannot be one of the disallowed field names')
        super(ParticipantPropertyName, self).validate(value)


class CustomDataField(db.EmbeddedDocument):
    name = ParticipantPropertyName()
    label = db.StringField()
    listview_visibility = db.BooleanField(default=False)

    def __unicode__(self):
        return self.name or u''


# Deployment
class Deployment(db.Document):
    name = db.StringField(required=True)
    hostnames = db.ListField(db.StringField())
    administrative_divisions_graph = db.StringField()
    participant_extra_fields = db.ListField(
        db.EmbeddedDocumentField(CustomDataField))
    allow_observer_submission_edit = db.BooleanField(
        default=True, verbose_name='Allow editing of Participant submissions?')
    logo = db.StringField()
    include_rejected_in_votes = db.BooleanField(default=False)
    is_initialized = db.BooleanField(default=False)
    dashboard_full_locations = db.BooleanField(
        default=True,
        verbose_name='Show all locations for dashboard stats?')

    meta = {
        'indexes': [
            ['hostnames']
        ]
    }

    def __unicode__(self):
        return self.name or u''


# Event
class Event(db.Document):
    name = db.StringField()
    start_date = db.DateTimeField(
        default=partial(datetime.combine, datetime.now(), datetime.min.time()))
    end_date = db.DateTimeField(
        default=partial(datetime.combine, datetime.now(), datetime.max.time()))

    deployment = db.ReferenceField(Deployment)

    meta = {
        'indexes': [
            ['deployment', 'name'],
            ['deployment', 'start_date', '-end_date']
        ]
    }

    def __unicode__(self):
        return self.name or u''
