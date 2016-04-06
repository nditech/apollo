from unittest import TestCase

from apollo.formsframework.models import FormField
from apollo.submissions.recordmanagers import PipelineBuilder

class AggregationManagerTest(TestCase):
    def test_first_projection_stage(self):
        manager = PipelineBuilder()

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

    def test_numeric_field_first_group_stage(self):
        manager = PipelineBuilder()

        # setup data
        field = FormField(name=u'AA')

        group_expr = manager._numeric_field_first_stage_group(field)
        token = u'${}'.format(field.name)

        self.assertIn(field.name, group_expr)
        self.assertEquals(group_expr[field.name], {u'$sum': token})

    def test_single_choice_field_first_group_stage(self):
        manager = PipelineBuilder()

        # setup data
        field = FormField(name='AA', options={u'Yes': 1,
                          u'No': 2, u'N/A': 3})

        group_expr = manager._single_choice_field_first_stage_group(field)
        token = u'${}'.format(field.name)

        for value in field.options.values():
            key_spec = u'{0}_{1}'.format(field.name, value)
            self.assertIn(key_spec, group_expr)
            value_expr = {
                u'$push': {u'$cond': [{u'$eq': [token, value]}, 1, 0]}
            }

            self.assertEquals(group_expr[key_spec], value_expr)

    def test_multiple_choice_field_first_group_stage(self):
        manager = PipelineBuilder()

        # setup data
        field = FormField(name='AA', options={u'Yes': 1,
                          u'No': 2, u'N/A': 3}, allows_multiple_values=True)
        token = u'${}'.format(field.name)

        group_expr = manager._multiple_choice_field_first_stage_group(field)

        self.assertIn(field.name, group_expr)
        self.assertEquals(group_expr[field.name], {u'$push': token})
