# -*- coding: utf-8 -*-
from apollo import create_app


class TestConfig(object):
    DEBUG = False
    TESTING = True
    TIMEZONE = "UTC"


def create_test_app():
    """Create the test application."""
    test_config = TestConfig()

    app = create_app(test_config)

    return app
