# -*- coding: utf-8 -*-
import pathlib

from apollo import create_app as create_full_app, settings
from apollo.factory import create_app


class TestConfig(object):
    TESTING = True
    TIMEZONE = 'UTC'

    def update(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def create_test_app():
    path = pathlib.Path().resolve().parent

    test_settings = {
        'SQLALCHEMY_DATABASE_URI': settings.TEST_DATABASE_URL
    }

    testConfig = TestConfig()
    testConfig.update(**test_settings)

    app = create_app('apollo', [str(path)], testConfig)

    return app


def create_full_test_app():
    test_settings = {
        'SQLALCHEMY_DATABASE_URI': settings.TEST_DATABASE_URL
    }

    testConfig = TestConfig()
    testConfig.update(**test_settings)

    app = create_full_app(testConfig)

    return app
