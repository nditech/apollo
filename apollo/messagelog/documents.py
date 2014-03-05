from mongoengine import *
from datetime import datetime


class Message(Document):
    sender = StringField()
    text = StringField()
    timestamp = DateTimeField(default=datetime.utcnow())
