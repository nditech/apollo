# # -*- coding: utf-8 -*-
import pathlib

import pytest
from werkzeug.datastructures import MultiDict

from apollo import services
from apollo.formsframework.forms import build_questionnaire, find_active_forms
from apollo.formsframework.models import Form
from apollo.formsframework.parser import Comparator, grammar_factory
from apollo.messaging.utils import parse_responses
from apollo.testutils import fixtures

DEFAULT_FIXTURE_PATH = pathlib.Path(__file__).parent / "fixtures"


class AttributeDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


@pytest.fixture()
def checklist_form():
    """Checklist form fixture."""
    grp1 = AttributeDict(name="First")
    grp1.fields = [
        AttributeDict(tag="AA", description="AA", type="integer"),
        AttributeDict(tag="AB", description="AB", type="multiselect", options={"One": 1, "Two": 2}),
    ]

    form = Form(name="TCF", form_type="CHECKLIST")
    form.data = {"groups": [grp1]}

    return form


@pytest.fixture()
def incident_form():
    """Critical incident form fixture."""
    grp2 = AttributeDict(name="Other", slug="Other")
    grp2.fields = [
        AttributeDict(tag="A", description="A", type="integer"),
        AttributeDict(tag="B", description="B", type="integer"),
    ]

    form = Form(name="TIF", form_type="INCIDENT")
    form.data = {"groups": [grp2]}

    return form


def test_checklist_parsing(checklist_form, mocker):
    """Test checklist form parsing."""
    filter_form = mocker.patch("apollo.formsframework.forms.filter_form")
    filter_participants = mocker.patch("apollo.formsframework.forms.filter_participants")
    filter_form.return_value = [checklist_form]
    filter_participants.return_value = []

    sample_text = "AA2AB12"
    q = build_questionnaire(checklist_form, MultiDict(parse_responses(sample_text, checklist_form)[0]))
    flag = q.validate()
    data = q.data

    assert data["AA"] == 2
    assert data["AB"] == [1, 2]
    # invalid due to missing data
    assert flag is False


def test_incident_parsing(incident_form, mocker):
    """Test critical incident form parsing."""
    filter_form = mocker.patch("apollo.formsframework.forms.filter_form")
    filter_participants = mocker.patch("apollo.formsframework.forms.filter_participants")
    filter_form.return_value = [incident_form]
    filter_participants.return_value = []

    sample_text = "A1B1"
    responses = parse_responses(sample_text, incident_form)[0]
    q = build_questionnaire(incident_form, MultiDict(responses))

    flag = q.validate()
    data = q.data
    assert data["A"] == 1
    assert data["B"] == 1
    assert flag is False


def test_numeric_comparisons():
    """Tests numeric comparisons."""
    comparator = Comparator()
    comparator.param = 4
    assert comparator.eval("> 3") is True
    assert comparator.eval("> 5") is False
    assert comparator.eval("< 5") is True
    assert comparator.eval("< 4") is False
    assert comparator.eval("<= 4") is True
    assert comparator.eval(">= 4") is True
    assert comparator.eval("= 4") is True
    assert comparator.eval("!= 4") is False
    assert comparator.eval("!= 10") is True


def test_boolean_comparisons():
    """Tests boolean comparisons."""
    comparator = Comparator()
    comparator.param = True
    assert comparator.eval("= True") is True
    assert comparator.eval("!= False") is True
    assert comparator.eval("= False") is False
    assert comparator.eval("!= True") is False
    assert comparator.eval(">= True") is True
    assert comparator.eval("<= True") is True


def test_operands():
    """Tests operands evaluation."""
    env = AttributeDict()
    env.data = AttributeDict()

    env.data.AA = 5
    env.data.AB = 3
    env.data.AC = 2

    evaluator = grammar_factory(env)

    assert evaluator("AA").expr() == 5
    assert evaluator("AB").expr() == 3
    assert evaluator("15").expr() == 15


def test_operations():
    """Tests operators."""
    env = AttributeDict()
    env.data = AttributeDict()

    env.data.AA = 5
    env.data.AB = 3
    env.data.AC = 2

    evaluator = grammar_factory(env)

    assert evaluator("AA + AB").expr() == 8
    assert evaluator("AA - AB").expr() == 2
    assert evaluator("AA * AB").expr() == 15
    assert evaluator("AB / AC").expr() == 1.5
    assert evaluator("AC ^ AB").expr() == 8
    assert evaluator("AA + 10").expr() == 15
    assert evaluator("AA + 5 ^ 3").expr() == 130
    assert evaluator("(AA + 5) ^ 3").expr() == 1000


def test_comparison_operators():
    """Tests comparison evaluations."""
    env = AttributeDict()
    env.data = AttributeDict()

    env.data.AA = 5
    env.data.AB = 3
    env.data.AC = 2
    env.data.AD = 2

    evaluator = grammar_factory(env)

    assert evaluator("AA > AB").expr() is True
    assert evaluator("AC < AB").expr() is True
    assert evaluator("AC > AB").expr() is False
    assert evaluator("AC <= AB").expr() is True
    assert evaluator("AC <= AD").expr() is True
    assert evaluator("AC >= AD").expr() is True
    assert evaluator("(AC + AD) > AB").expr() is True
    assert evaluator("AC + AD > AB").expr() is True
    assert evaluator("(AB + AA) < 9").expr() is True
    assert evaluator("AB + AA < 9").expr() is True
    assert evaluator("AA + AB == 8").expr() is True
    assert evaluator("(AA + AC) != ((AB + AD))").expr() is True


def test_logic_operators():
    """Tests logic operators."""
    env = AttributeDict()
    env.data = AttributeDict()

    env.data.AA = 5
    env.data.AB = 3
    env.data.AC = 2
    env.data.AD = 2

    evaluator = grammar_factory(env)

    assert evaluator("AA > AB && AC >= AD").expr() is True
    assert evaluator("AA < AB || (AC >= AD)").expr() is True
    assert evaluator("AA < AB || AC >= AD && AA == 5").expr() is True


def test_active_form_selector(app, mocker):
    """Tests form selection based on chosen event."""
    fixture_path = DEFAULT_FIXTURE_PATH / "38fff911ea3.sql"
    fixtures.load_sql_fixture(fixture_path)

    event1, event2, event3 = services.events.find().order_by("id").all()
    form1, form2, form3, form4, form5, form6 = services.forms.find().order_by("id").all()

    mocker.patch.object(services.events, "default", return_value=event1)
    forms = find_active_forms().all()
    assert form1 in forms
    assert form2 in forms
    assert form3 not in forms
    assert form4 not in forms
    assert form5 not in forms
    assert form6 not in forms

    mocker.patch.object(services.events, "default", return_value=event2)
    forms = find_active_forms().all()
    assert form1 not in forms
    assert form2 not in forms
    assert form3 in forms
    assert form4 in forms
    assert form5 in forms
    assert form6 in forms

    mocker.patch.object(services.events, "default", return_value=event2)
    forms = find_active_forms().all()
    assert form1 not in forms
    assert form2 not in forms
    assert form3 in forms
    assert form4 in forms
    assert form5 in forms
    assert form6 in forms
