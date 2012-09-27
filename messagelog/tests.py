"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from rapidsms.tests.scripted import TestScript
from .models import *


class MessageLogTestScript(TestScript):
    def test_logging(self):
        logcount = MessageLog.objects.count()
        self.assertInteraction('''
            12345 > Hello
            12345 > Goodbye
        ''')
        count = MessageLog.objects.filter(direction=MESSAGE_OUTGOING).count()
        self.assertEqual((logcount + 2), count)
