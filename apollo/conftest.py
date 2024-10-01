import pytest
from sqlalchemy import text
from sqlalchemy_utils import create_database, database_exists, drop_database

from apollo.core import db as _db
from apollo.testutils.factory import create_test_app


@pytest.fixture(scope="module", autouse=True)
def app():
    """Flask app fixture."""
    app = create_test_app()

    if database_exists(app.config.get("SQLALCHEMY_DATABASE_URI")):
        drop_database(app.config.get("SQLALCHEMY_DATABASE_URI"))
    create_database(app.config.get("SQLALCHEMY_DATABASE_URI"))

    with app.test_request_context():
        with _db.engine.connect() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
            connection.execute(text("COMMIT"))

        _db.create_all()

        yield app

        _db.session.close()
        _db.drop_all()


@pytest.fixture()
def db(app):
    """Database fixture."""
    return _db
