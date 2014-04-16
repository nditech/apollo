from ..core import Service
from .models import Message
from flask import g


class MessagesService(Service):
    __model__ = Message

    def log_message(self, direction, text, recipient="", sender=""):
        return self.create(
            direction=direction, recipient=recipient, sender=sender,
            text=text, deployment=g.deployment, event=g.event)

    def all(self):
        """Returns a generator containing all instances of the service's model.
        """
        return self.__model__.objects.filter(
            deployment=g.deployment, event=g.event)
