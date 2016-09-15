import os
import warnings
from flask.ext.testing import TestCase
from werkzeug.datastructures import MultiDict
from apollo import create_app
from apollo.messaging.utils import parse_responses
from apollo.formsframework.forms import build_questionnaire
from apollo.formsframework.models import Form, FormField, FormGroup
from apollo.formsframework.parser import Comparator, grammar_factory


ENV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')


def read_env(env_path=None):
    if env_path is None:
        env_path = os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(env_path):
        warnings.warn('No environment file found. Skipping load.')
        return

    for k, v in parse_env(env_path):
        os.environ.setdefault(k, v)


def parse_env(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            v = v.strip('"').strip("'")
            yield k, v


class QuestionnaireTest(TestCase):
    def create_app(self):
        read_env(ENV_PATH)
        return create_app()

    def setUp(self):
        aa = FormField(name='AA', description='AA')
        ab = FormField(name='AB', description='AB',
                       allows_multiple_values=True,
                       options={'1': 'One', '2': 'Two'})

        grp1 = FormGroup(name='First', slug='First')
        grp1.fields.append(aa)
        grp1.fields.append(ab)

        self.checklist_form = Form(name='TCF', form_type='CHECKLIST')
        self.checklist_form.groups.append(grp1)

        a = FormField(name='A', description='A', represents_boolean=True)
        b = FormField(name='B', description='B', represents_boolean=True)

        grp2 = FormGroup(name='Other', slug='Other')
        grp2.fields.append(a)
        grp2.fields.append(b)

        self.incident_form = Form(name='TIF', form_type='INCIDENT')
        self.incident_form.groups.append(grp2)

    def test_checklist_parsing(self):
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

    def test_incident_parsing(self):
        sample_text = 'AB'
        responses = parse_responses(sample_text, self.incident_form)[0]
        q = build_questionnaire(self.incident_form, MultiDict(responses))

        flag = q.validate()
        data = q.data
        self.assertEqual(data['A'], 1)
        self.assertEqual(data['B'], 1)
        self.assertFalse(flag)


class ComparatorTest(TestCase):
    def create_app(self):
        read_env(ENV_PATH)
        return create_app()

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
    def create_app(self):
        read_env(ENV_PATH)
        return create_app()

    def setUp(self):
        class AttributeHolder(object):
            def set(self, attr, value):
                setattr(self, attr, value)

        self.env = AttributeHolder()

    def test_operands(self):
        self.env.set('AA', 5)
        self.env.set('AB', 3)
        self.env.set('AC', 2)

        evaluator = grammar_factory(self.env)

        self.assertEqual(evaluator('AA').expr(), 5)
        self.assertEqual(evaluator('AB').expr(), 3)
        self.assertEqual(evaluator('15').expr(), 15)

    def test_operations(self):
        self.env.set('AA', 5)
        self.env.set('AB', 3)
        self.env.set('AC', 2)

        evaluator = grammar_factory(self.env)

        self.assertEqual(evaluator('AA + AB').expr(), 8)
        self.assertEqual(evaluator('AA - AB').expr(), 2)
        self.assertEqual(evaluator('AA * AB').expr(), 15)
        self.assertEqual(evaluator('AB / AC').expr(), 1.5)
        self.assertEqual(evaluator('AC ^ AB').expr(), 8)
        self.assertEqual(evaluator('AA + 10').expr(), 15)
        self.assertEqual(evaluator('AA + 5 ^ 3').expr(), 130)
        self.assertEqual(evaluator('(AA + 5) ^ 3').expr(), 1000)
