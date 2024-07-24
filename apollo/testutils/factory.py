# -*- coding: utf-8 -*-
from apollo import settings
from apollo import create_app


class TestConfig(object):
    TESTING = True
    TIMEZONE = 'UTC'
    DEBUG = False

    def update(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def create_test_app():
    test_settings = {
        'SQLALCHEMY_DATABASE_URI': settings.TEST_DATABASE_URL,
    }

    testConfig = TestConfig()
    testConfig.update(**test_settings)

    app = create_app(testConfig)

    return app
