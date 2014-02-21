from django.conf import settings
from django.test import simple, testcases
from django.utils import unittest

from mongoengine import connect, connection
from mongoengine.django import tests


class MongoEngineTestSuiteRunner(simple.DjangoTestSuiteRunner):
    """
    It is the same as in DjangoTestSuiteRunner,
    but without relational databases.

    It also supports filtering only wanted tests through ``TEST_RUNNER_FILTER``
    Django setting.
    """

    db_name = 'test_%s' % settings.MONGO_DATABASE_NAME

    def _filter_suite(self, suite):
        filters = getattr(settings, 'TEST_RUNNER_FILTER', None)

        if filters is None:
            # We do NOT filter if filters are not set
            return suite

        filtered = unittest.TestSuite()

        for test in suite:
            if isinstance(test, unittest.TestSuite):
                filtered.addTests(self._filter_suite(test))
            else:
                for f in filters:
                    if test.id().startswith(f):
                        filtered.addTest(test)

        return filtered

    def build_suite(self, test_labels, extra_tests=None, **kwargs):
        suite = super(MongoEngineTestSuiteRunner, self) \
            .build_suite(test_labels, extra_tests=None, **kwargs)
        suite = self._filter_suite(suite)
        return simple.runner.reorder_suite(suite, (testcases.TestCase,))

    def setup_databases(self, **kwargs):
        connection.disconnect()
        connect(self.db_name, host=settings.MONGO_DATABASE_HOST)

    def teardown_databases(self, old_config, **kwargs):
        connection.get_connection().drop_database(self.db_name)


class MongoEngineTestCase(tests.MongoTestCase):
    """
    A bugfixed version, see this `pull request`_.

    .. _pull request: https://github.com/hmarr/mongoengine/pull/506
    """

    def __init__(self, methodName='runtest'):
        # We skip MongoTestCase init
        super(tests.MongoTestCase, self).__init__(methodName)

    def _post_teardown(self):
        self.db = connection.get_db()
        super(MongoEngineTestCase, self)._post_teardown()
