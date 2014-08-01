from ..core import Service
from .models import Message, Gateway
from datetime import datetime
from flask import g
from unidecode import unidecode
import csv
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO


class MessagesService(Service):
    __model__ = Message

    def log_message(self, event, direction, text, recipient="", sender=""):
        return self.create(
            direction=direction, recipient=recipient, sender=sender,
            text=text, deployment=event.deployment, event=event,
            received=datetime.utcnow())

    def all(self):
        """Returns a generator containing all instances of the service's model.
        """
        return self.__model__.objects.filter(
            deployment=g.deployment, event=g.event)

    def export_list(self, queryset):
        headers = [
            'Mobile', 'Text', 'Direction', 'Created', 'Delivered'
        ]
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([unidecode(unicode(i)) for i in headers])
        yield output.getvalue()
        output.close()

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

            record = [unidecode(i) for i in record]

            output = StringIO()
            writer = csv.writer(output)
            writer.writerow([unidecode(unicode(i)) for i in record])
            yield output.getvalue()
            output.close()


class GatewayService(Service):
    __model__ = Gateway
