from unittest import TestCase

from apollo.formsframework.models import FormField
from apollo.submissions.recordmanagers import (
    AggregationFrameworkRecordManager2)


class AggregationManagerTest(TestCase):
    def test_first_projection_stage(self):
        manager = AggregationFrameworkRecordManager2()

        # setup data
        first_stage_project_fields = [
            FormField(name=u'AA'),
            FormField(name=u'AB'),
            FormField(name=u'BA'),
            FormField(name=u'BB'),
            FormField(name=u'BC')
        ]
        first_stage_location_types = [
            u'Country',
            u'Political Region',
            u'Region',
            u'District',
            u'Constituency',
            u'Parish',
        ]

        project_stage = manager.generate_first_stage_project(
            first_stage_project_fields,
            first_stage_location_types)

        for fi in first_stage_project_fields:
            self.assertIn(fi.name, project_stage)
            self.assertEquals(project_stage[fi.name], 1)

        for lt in first_stage_location_types:
            self.assertIn(lt, project_stage[u'location_name_path'])
            self.assertEquals(project_stage[u'location_name_path'][lt], 1)

        self.assertIn(u'_id', project_stage)
        self.assertEquals(project_stage[u'_id'], 0)
