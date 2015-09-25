from datetime import datetime
from apollo.core import db
from apollo.deployments.models import Deployment, Event
from apollo.participants.models import Participant
from apollo.submissions.models import Submission


class Message(db.Document):
    DIRECTIONS = (
        ('IN', 'INCOMING'),
        ('OUT', 'OUTGOING'))

    direction = db.StringField(choices=DIRECTIONS)
    recipient = db.StringField()
    sender = db.StringField()
    text = db.StringField()
    participant = db.ReferenceField(Participant)
    submission = db.ReferenceField(Submission)
    received = db.DateTimeField(default=datetime.utcnow)
    delivered = db.DateTimeField()

    deployment = db.ReferenceField(Deployment)
    event = db.ReferenceField(Event)

    meta = {
        'indexes': [
            ['sender'],
            ['recipient'],
            ['text'],
            ['participant'],
            ['submission'],
            ['received'],
            ['delivered'],
            ['deployment'],
            ['deployment', 'event']
        ]
    }
