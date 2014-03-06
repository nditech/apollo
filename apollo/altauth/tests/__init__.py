from __future__ import unicode_literals
from mongoengine import connect

TEST_DATABASE = 'apollo_test'


class Suite(object):
    connection = None


def setup():
    Suite.connection = connect(TEST_DATABASE)


def teardown():
    Suite.connection.drop_database(TEST_DATABASE)
    Suite.connection.close()
