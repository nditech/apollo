from rapidsms.apps.base import AppBase
from .models import *


class App(AppBase):
    def parse(self, message):
        MessageLog.objects.create(direction=MESSAGE_INCOMING,
            text=message.text, sender=message.peer)
        return False

    def outgoing(self, message):
        MessageLog.objects.create(direction=MESSAGE_OUTGOING,
            text=message.text, sender=message.peer)
        return True
