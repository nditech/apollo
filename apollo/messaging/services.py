# -*- coding: utf-8 -*-
from datetime import datetime

from apollo.dal.service import Service
from apollo.messaging.models import Message


class MessageService(Service):
    __model__ = Message

    def log_message(self, event, direction, text, recipient='', sender='',
                    timestamp=None):
        if timestamp:
            try:
                msg_time = datetime.utcfromtimestamp(timestamp)
            except ValueError:
                msg_time = datetime.utcnow()
        else:
            msg_time = datetime.utcnow()

        return self.create(
            direction=direction, recipient=recipient, sender=sender, text=text,
            deployment_id=event.deployment_id, event=event, received=msg_time)
