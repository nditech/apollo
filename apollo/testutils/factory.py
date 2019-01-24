# -*- coding: utf-8 -*-
import pathlib

from apollo.factory import create_app


class TestConfig(object):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'postgres://localhost/apollo_test'
    TIMEZONE = 'UTC'


def create_test_app():
    path = pathlib.Path().resolve().parent
    testConfig = TestConfig()

    app = create_app('apollo', [str(path)], testConfig)

    return app
