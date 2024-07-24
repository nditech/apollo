import chromedriver_autoinstaller
import pytest
from flask_migrate import upgrade
from selenium import webdriver
from sqlalchemy_utils import create_database, database_exists, drop_database

from apollo.testutils.factory import create_test_app


@pytest.fixture(scope='session')
def app():
    app = create_test_app()
    with app.app_context():
        if database_exists(app.config.get('SQLALCHEMY_DATABASE_URI')):
            drop_database(app.config.get('SQLALCHEMY_DATABASE_URI'))
        create_database(app.config.get('SQLALCHEMY_DATABASE_URI'))
        upgrade()

    yield app

    with app.app_context():
        drop_database(app.config.get('SQLALCHEMY_DATABASE_URI'))

@pytest.fixture(scope="session")
def driver():
    chromedriver_autoinstaller.install()

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    options.add_argument("--incognito")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1920, 1080)

    yield driver

    driver.stop_client()
    driver.quit()
