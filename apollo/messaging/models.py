from datetime import datetime
from ..core import db
from ..deployments.models import Deployment, Event
from ..participants.models import Participant
from ..submissions.models import Submission


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
