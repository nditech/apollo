from ..core import db


# Deployment
class Deployment(db.Document):
    name = db.StringField(required=True)
    hostnames = db.ListField(db.StringField())
    administrative_divisions_graph = db.StringField()

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
