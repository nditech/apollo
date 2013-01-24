"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from rapidsms.router.api import lookup_connections
from rapidsms.tests.scripted import TestScript
from outboundsms.tasks import _send_message


class OutboundSMSTest(TestScript):
    def test_message_sending(self):
        '''Test to confirm message sending occurs'''
        connections = lookup_connections('httptester', ['1234'])

        _send_message(connections[0], 'Hello, world!')

        self.assertInteraction('1234 < Hello, world!')
