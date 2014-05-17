from ..core import db


class CustomDataField(db.EmbeddedDocument):
    name = db.StringField()
    label = db.StringField()


# Deployment
class Deployment(db.Document):
    name = db.StringField(required=True)
    hostnames = db.ListField(db.StringField())
    administrative_divisions_graph = db.StringField()
    participant_extra_fields = db.ListField(
        db.EmbeddedDocumentField(CustomDataField))
    allow_observer_submission_edit = db.BooleanField(default=True)
    logo = db.StringField()
    include_rejected_in_votes = db.BooleanField(default=False)

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

    def __unicode__(self):
        return self.name
