import pytest
from apollo.testutils.factory import create_test_app
from sqlalchemy_utils import database_exists, create_database, drop_database
from apollo.core import db


@pytest.fixture(scope='module', autouse=True)
def app():
    app = create_test_app()
    with app.app_context():
        if database_exists(app.config.get('SQLALCHEMY_DATABASE_URI')):
            drop_database(app.config.get('SQLALCHEMY_DATABASE_URI'))
        create_database(app.config.get('SQLALCHEMY_DATABASE_URI'))
        with db.engine.connect() as connection:
            connection.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

    yield app
