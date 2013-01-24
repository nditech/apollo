"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from csv import DictReader
from StringIO import StringIO
from django.test.client import Client
from rapidsms.tests.scripted import TestScript
from .models import *


class MessageLogTestScript(TestScript):
    def test_message_logging(self):
        # add some messages to the queue
        self.assertInteraction('''
            12345 > Hello
            12345 < Invalid message: "He110". Please check and resend!
            ''')

        c = Client()
        response = c.get('/messagelog/export/csv/')


        self.assertEquals(response.status_code, 200)

        csvfile = StringIO(response.content)
        reader = DictReader(csvfile)

        row = reader.next()

        self.assertEquals(row['Mobile'], '12345')
        self.assertEquals(row['Text'], 'Hello')
        self.assertEquals(row['Message direction'], 'Incoming')

        row = reader.next()

        self.assertEquals(row['Message direction'], 'Outgoing')
