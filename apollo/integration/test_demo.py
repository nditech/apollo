import chromedriver_autoinstaller
import pytest
from flask_migrate import upgrade
from flask_testing import LiveServerTestCase
from selenium import webdriver
from sqlalchemy.orm.session import close_all_sessions

from apollo.core import db
from apollo.testutils import factory as test_factory


class DemoTest(LiveServerTestCase):
    def create_app(self):
        app = test_factory.create_test_app()
        app.config['LIVESERVER_PORT'] = 8943
        return app

    def setUp(self):
        with self.app.app_context():
            upgrade()

        chromedriver_autoinstaller.install()

        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--no-sandbox")
        options.add_argument("--incognito")
        options.add_argument("--disable-dev-shm-usage")

        self.browser = webdriver.Chrome(options=options)

    def tearDown(self):
        self.browser.quit()
        close_all_sessions()
        db.drop_all()
        db.engine.execute("DROP TABLE alembic_version")

    @pytest.mark.filterwarnings("ignore::DeprecationWarning")
    def test_server_is_up_and_running(self):
        self.browser.get(self.get_server_url())
        assert "Apollo" in self.browser.page_source
