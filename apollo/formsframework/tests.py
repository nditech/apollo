import os
import warnings
from flask.ext.testing import TestCase
from werkzeug.datastructures import MultiDict
from apollo.frontend import create_app
from .forms import build_questionnaire
from .models import Form, FormField, FormGroup


env_path = os.path.join(
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
        read_env(env_path)
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
        q = build_questionnaire(self.checklist_form, MultiDict({'AA': 2}))
        flag = q.validate()

        self.assertTrue(flag)
