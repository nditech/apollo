# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from dateutil.tz import gettz
from flask_testing import TestCase

from apollo import create_app, models, settings
from apollo.core import db
from apollo.odk import utils


class ODKTest(TestCase):
    def create_app(self):
        return create_app()

    def setUp(self):
        db.create_all()
        self._setup_fixtures()

    def tearDown(self):
        db.session.close()
        db.drop_all()

    def _setup_fixtures(self):
        self._deployment = models.Deployment(
            name='Test', hostnames=['localhost']
        )

        time_zone = gettz(settings.TIMEZONE)
        current_timestamp = datetime.now(time_zone)

        start = current_timestamp.replace(hour=0, minute=0, second=0,
                                          microsecond=0)
        end = current_timestamp.replace(hour=23, minute=59, second=59,
                                        microsecond=999999)

        start2 = start + timedelta(days=1)
        end2 = end + timedelta(days=1)

        self._form_set_1 = models.FormSet(name='Form Set 1', deployment=self._deployment)
        self._form_set_2 = models.FormSet(name='Form Set 2', deployment=self._deployment)

        self._location_set_1 = models.LocationSet(name='Location Set 1',
                                                  deployment=self._deployment)
        self._location_set_2 = models.LocationSet(name='Location Set 2',
                                                  deployment=self._deployment)

        self._form1 = models.Form(name='Form 1', prefix='XA',
                                  deployment=self._deployment, form_type='CHECKLIST',
                                  form_set=self._form_set_1)
        self._form2 = models.Form(name='Form 2', prefix='XB',
                                  deployment=self._deployment, form_type='CHECKLIST',
                                  form_set=self._form_set_1)
        self._form3 = models.Form(name='Form 3', prefix='XC',
                                  deployment=self._deployment, form_type='CHECKLIST',
                                  form_set=self._form_set_2)

        self._event1 = models.Event(name='Event 1', deployment=self._deployment,
                                    start=start, end=end, form_set=self._form_set_1)
        self._event2 = models.Event(name='Event 2', deployment=self._deployment,
                                    start=start, end=end, form_set=self._form_set_2)
        self._event3 = models.Event(name='Event 3', deployment=self._deployment,
                                    start=start2, end=end2, form_set=self._form_set_1)

        db.session.add_all([
            self._deployment,
            self._form_set_1,
            self._form_set_2,
            self._form1,
            self._form2,
            self._form3,
            self._event1,
            self._event2,
            self._event3,
        ])
        db.session.commit()

    def test_form_selection(self):
        selected_forms = utils.get_forms_for_event(self._event1)

        self.assertEqual(len(selected_forms), 3)
        self.assertIn(self._form1, selected_forms)
        self.assertIn(self._form2, selected_forms)
