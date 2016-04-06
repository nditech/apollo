from unittest import TestCase

from apollo.formsframework.models import FormField
from apollo.submissions.recordmanagers import AggregationFrameworkRecordManager2


class AggregationManagerTest(TestCase):
    def setUp(self):
        self.first_stage_project_fields = [
            FormField(name=u'AA'),
            FormField(name=u'AB'),
            FormField(name=u'BA'),
            FormField(name=u'BB'),
            FormField(name=u'BC')
        ]

    def test_first_projection_stage(self):
        manager = AggregationFrameworkRecordManager2()

        project_stage = manager.generate_first_stage_project(
            self.first_stage_project_fields)

        for fi in self.first_stage_project_fields:
            self.assertIn(fi.name, project_stage)
            self.assertEquals(project_stage[fi.name], 1)
