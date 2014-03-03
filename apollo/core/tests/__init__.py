from __future__ import unicode_literals
import os
from unittest import TestCase
from mongoengine.connection import connect, disconnect
from core.tests.utils import load_fixtures

FIXTURES_PATH = os.path.join(
    os.path.abspath(os.path.dirname(os.path.dirname(__file__))),
    'tests/fixtures'
)
TEST_DATABASE = 'apollo_test'


class Suite(object):
    connection = None


def setup():
    # we're not going to be using the default connection
    disconnect()
    Suite.connection = connect(TEST_DATABASE)


def teardown():
    Suite.connection.drop_database(TEST_DATABASE)
    Suite.connection.close()


def setup_fixtures(filename):
    path_getter = os.path.join(FIXTURES_PATH, filename)
    load_fixtures(Suite.connection[TEST_DATABASE], path_getter)


class BaseTestCase(TestCase):
    def setUp(self):
        if hasattr(self, 'fixtures'):
            setup_fixtures(getattr(self, 'fixtures'))
        return super(BaseTestCase, self).setUp()
