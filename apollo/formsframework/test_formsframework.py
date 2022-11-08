# -*- coding: utf-8 -*-
import pathlib
from unittest import mock

from flask_testing import TestCase
from werkzeug.datastructures import MultiDict

from apollo import services
from apollo.core import db
from apollo.messaging.utils import parse_responses
from apollo.formsframework.forms import build_questionnaire, find_active_forms
from apollo.formsframework.models import Form
from apollo.formsframework.parser import Comparator, grammar_factory
from apollo.testutils import factory as test_factory, fixtures

DEFAULT_FIXTURE_PATH = pathlib.Path(__file__).parent / 'fixtures'


class AttributeDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


class QuestionnaireTest(TestCase):
    def create_app(self):  # noqa
        return test_factory.create_test_app()

    def setUp(self):
        db.create_all()

        aa = AttributeDict(tag='AA', description='AA', type='integer')
        ab = AttributeDict(tag='AB', description='AB', type='multiselect',
                           options={'1': 'One', '2': 'Two'})

        grp1 = AttributeDict(name='First')
        grp1.fields = []
        grp1.fields.append(aa)
        grp1.fields.append(ab)

        self.checklist_form = Form(name='TCF', form_type='CHECKLIST')
        self.checklist_form.data = {'groups': [grp1]}

        a = AttributeDict(tag='A', description='A', type='integer')
        b = AttributeDict(tag='B', description='B', type='integer')

        grp2 = AttributeDict(name='Other', slug='Other')
        grp2.fields = []
        grp2.fields.append(a)
        grp2.fields.append(b)

        self.incident_form = Form(name='TIF', form_type='INCIDENT')
        self.incident_form.data = {'groups': [grp2]}

    def tearDown(self):
        db.session.close_all()
        db.drop_all()

    @mock.patch('apollo.formsframework.forms.filter_form')
    @mock.patch('apollo.formsframework.forms.filter_participants')
    def test_checklist_parsing(self, filter_form, filter_participants):
        filter_form.return_value = [self.checklist_form]
        filter_participants.return_value = []

        sample_text = 'AA2AB12'
        q = build_questionnaire(
            self.checklist_form,
            MultiDict(parse_responses(sample_text, self.checklist_form)[0]))
        flag = q.validate()
        data = q.data

        self.assertEqual(data['AA'], 2)
        self.assertEqual(data['AB'], [1, 2])
        # invalid due to missing data
        self.assertFalse(flag)

    @mock.patch('apollo.formsframework.forms.filter_form')
    @mock.patch('apollo.formsframework.forms.filter_participants')
    def test_incident_parsing(self, filter_form, filter_participants):
        filter_form.return_value = [self.checklist_form]
        filter_participants.return_value = []

        sample_text = 'A1B1'
        responses = parse_responses(sample_text, self.incident_form)[0]
        q = build_questionnaire(self.incident_form, MultiDict(responses))

        flag = q.validate()
        data = q.data
        self.assertEqual(data['A'], 1)
        self.assertEqual(data['B'], 1)
        self.assertFalse(flag)


class ComparatorTest(TestCase):
    def create_app(self):  # noqa
        return test_factory.create_test_app()

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.close_all()
        db.drop_all()

    def test_numeric_comparisons(self):
        comparator = Comparator()
        comparator.param = 4
        self.assertTrue(comparator.eval('> 3'))
        self.assertFalse(comparator.eval('> 5'))
        self.assertTrue(comparator.eval('< 5'))
        self.assertFalse(comparator.eval('< 4'))
        self.assertTrue(comparator.eval('<= 4'))
        self.assertTrue(comparator.eval('>= 4'))
        self.assertTrue(comparator.eval('= 4'))
        self.assertFalse(comparator.eval('!= 4'))
        self.assertTrue(comparator.eval('!= 10'))

    def test_boolean_comparisons(self):
        comparator = Comparator()
        comparator.param = True
        self.assertTrue(comparator.eval('= True'))
        self.assertTrue(comparator.eval('!= False'))
        self.assertFalse(comparator.eval('= False'))
        self.assertFalse(comparator.eval('!= True'))
        self.assertTrue(comparator.eval('>= True'))
        self.assertTrue(comparator.eval('<= True'))


class GrammarTest(TestCase):
    def create_app(self):  # noqa
        return test_factory.create_test_app()

    def setUp(self):
        self.env = AttributeDict()
        self.env.data = AttributeDict()

    def test_operands(self):
        self.env.data.AA = 5
        self.env.data.AB = 3
        self.env.data.AC = 2

        evaluator = grammar_factory(self.env)

        self.assertEqual(evaluator('AA').expr(), 5)
        self.assertEqual(evaluator('AB').expr(), 3)
        self.assertEqual(evaluator('15').expr(), 15)

    def test_operations(self):
        self.env.data.AA = 5
        self.env.data.AB = 3
        self.env.data.AC = 2

        evaluator = grammar_factory(self.env)

        self.assertEqual(evaluator('AA + AB').expr(), 8)
        self.assertEqual(evaluator('AA - AB').expr(), 2)
        self.assertEqual(evaluator('AA * AB').expr(), 15)
        self.assertEqual(evaluator('AB / AC').expr(), 1.5)
        self.assertEqual(evaluator('AC ^ AB').expr(), 8)
        self.assertEqual(evaluator('AA + 10').expr(), 15)
        self.assertEqual(evaluator('AA + 5 ^ 3').expr(), 130)
        self.assertEqual(evaluator('(AA + 5) ^ 3').expr(), 1000)

    def test_comparison_operators(self):
        self.env.data.AA = 5
        self.env.data.AB = 3
        self.env.data.AC = 2
        self.env.data.AD = 2

        evaluator = grammar_factory(self.env)

        self.assertTrue(evaluator('AA > AB').expr())
        self.assertTrue(evaluator('AC < AB').expr())
        self.assertFalse(evaluator('AC > AB').expr())
        self.assertTrue(evaluator('AC <= AB').expr())
        self.assertTrue(evaluator('AC <= AD').expr())
        self.assertTrue(evaluator('AC >= AD').expr())
        self.assertTrue(evaluator('(AC + AD) > AB').expr())
        self.assertTrue(evaluator('AC + AD > AB').expr())
        self.assertTrue(evaluator('(AB + AA) < 9').expr())
        self.assertTrue(evaluator('AB + AA < 9').expr())
        self.assertTrue(evaluator('AA + AB == 8').expr())
        self.assertTrue(evaluator('(AA + AC) != ((AB + AD))').expr())

    def test_logic_operators(self):
        self.env.data.AA = 5
        self.env.data.AB = 3
        self.env.data.AC = 2
        self.env.data.AD = 2

        evaluator = grammar_factory(self.env)

        self.assertTrue(evaluator('AA > AB && AC >= AD').expr())
        self.assertTrue(evaluator('AA < AB || (AC >= AD)').expr())
        self.assertTrue(evaluator('AA < AB || AC >= AD && AA == 5').expr())


class FormUtilsTest(TestCase):
    def create_app(self):
        return test_factory.create_test_app()

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.close_all()
        db.drop_all()

    def test_active_form_selector(self):
        fixture_path = DEFAULT_FIXTURE_PATH / '38fff911ea3.sql'
        fixtures.load_sql_fixture(fixture_path)

        event1, event2, event3 = services.events.find().order_by('id').all()
        form1, form2, form3, form4, form5, form6 = services.forms.find(
            ).order_by('id').all()

        with mock.patch.object(
                services.events, 'default', return_value=event1):
            forms = find_active_forms().all()
            self.assertIn(form1, forms)
            self.assertIn(form2, forms)
            self.assertNotIn(form3, forms)
            self.assertNotIn(form4, forms)
            self.assertNotIn(form5, forms)
            self.assertNotIn(form6, forms)

        with mock.patch.object(
                services.events, 'default', return_value=event2):
            forms = find_active_forms().all()
            self.assertNotIn(form1, forms)
            self.assertNotIn(form2, forms)
            self.assertIn(form3, forms)
            self.assertIn(form4, forms)
            self.assertIn(form5, forms)
            self.assertIn(form6, forms)

        with mock.patch.object(
                services.events, 'default', return_value=event3):
            forms = find_active_forms().all()
            self.assertNotIn(form1, forms)
            self.assertNotIn(form2, forms)
            self.assertIn(form3, forms)
            self.assertIn(form4, forms)
            self.assertIn(form5, forms)
            self.assertIn(form6, forms)
