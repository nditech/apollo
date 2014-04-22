from ..core import Service
from .models import Message
from flask import g
from tablib import Dataset


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

    def export_list(self, queryset):
        ds = Dataset(
            headers=[
                'Mobile', 'Text', 'Direction', 'Created', 'Delivered'
            ]
        )

        for message in queryset:
            # limit to three numbers for export and pad if less than three
            record = [
                message.sender if message.direction == 'IN'
                else message.recipient,
                message.text,
                message.direction,
                message.received.strftime('%Y-%m-%d %H:%M:%S')
                if message.received else '',
                message.delivered.strftime('%Y-%m-%d %H:%M:%S')
                if message.delivered else ''
            ]

            ds.append(record)

        return ds
