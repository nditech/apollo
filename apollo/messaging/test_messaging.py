# -*- coding: utf-8 -*-
import pathlib
from datetime import datetime

import flask_babel as babel
import pytest
from flask_babel import force_locale
from mimesis import Generic
from mimesis.locales import Locale

from apollo import services
from apollo.formsframework.models import Form
from apollo.messaging.helpers import lookup_participant
from apollo.messaging.utils import get_unsent_codes, parse_responses, parse_text
from apollo.testutils import fixtures

DEFAULT_FIXTURES_PATH = pathlib.Path(__file__).parent / "fixtures"


class AttributeDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


@pytest.fixture
def form():
    """Test form fixture."""
    a = AttributeDict(name="Group 1")
    a.fields = [
        AttributeDict(tag="AA", type="integer"),
        AttributeDict(tag="BA", type="integer"),
        AttributeDict(tag="Comment1", type="comment"),
    ]

    b = AttributeDict(name="Group 2")
    b.fields = [
        AttributeDict(tag="D", type="integer"),
        AttributeDict(tag="EA", type="multiselect"),
        AttributeDict(tag="Comment2", type="comment"),
    ]

    form = Form()
    form.data = {"groups": [a, b]}

    return form


def test_response_parsing(form):
    """Tests correct parsing of text."""
    assert parse_responses("", form)[0] == {}
    assert parse_responses("AA1BA2", form)[0] == {"AA": "1", "BA": "2"}
    assert parse_responses("EA135DBAAA3", form)[0] == {"AA": "3", "EA": "135"}
    assert "Comment1" not in parse_responses("EA135DBAAA3", form)[0]
    assert parse_responses("ZX1CV2EA135DBAAA3", form)[0] == {"AA": "3", "EA": "135"}


def test_leftover_processing(form):
    """Tests correct processing of extraneous content."""
    assert parse_responses("ZX1CV2EA135DBAAA3", form)[1] == "ZX1CV2DBA"
    assert parse_responses("ZX1CV2EA135DBAAA3THIS IS A TEST", form)[1] == "ZX1CV2DBATHIS IS A TEST"
    assert parse_responses("ZX1CV2EA135DBAAA3 THIS IS A TEST ", form)[1] == "ZX1CV2DBA THIS IS A TEST"


def test_partial_response(form):
    """Test partial response generation."""
    assert get_unsent_codes(form, ["AA", "BA"]) == ["Comment1"]
    assert get_unsent_codes(form, ["D", "Comment2"]) == ["EA"]


def test_full_response(form):
    """Test complete response generation."""
    assert get_unsent_codes(form, ["AA", "BA", "Comment1"]) is None


def test_parse_invalid_message():
    """Test invalid message."""
    sample_text = "2014"
    result = parse_text(sample_text)
    (prefix, participant_id, exclamation, form_serial, responses, comment) = result

    assert prefix is None
    assert participant_id is None, sample_text
    assert exclamation is None
    assert form_serial is None
    assert responses is None
    assert comment is None


def test_parse_survey_message():
    """Test parsing a survey message."""
    sample_text = "TC111111X321AA2"
    result = parse_text(sample_text)
    (prefix, participant_id, exclamation, form_serial, responses, comment) = result

    assert prefix == "TC"
    assert participant_id == "111111"
    assert exclamation is False
    assert form_serial == "321"
    assert responses == "AA2"
    assert comment is None


@pytest.mark.parametrize("locale", ["EN", "ES", "FA", "FR", "RU"])
def test_parse_comment_message(locale):
    """Tests message comment."""
    faker = Generic()

    # test with comments in the locales below
    # we're using Farsi instead of Arabic
    # as mimesis doesn't support Arabic yet ):
    current_locale = getattr(Locale, locale)
    test_participant_id = faker.person.identifier("######")

    with faker.text.override_locale(current_locale):
        test_comment = faker.text.sentence()
        sample_text = "XA{}AA1AB2@{}".format(test_participant_id, test_comment)

        result = parse_text(sample_text)
        (prefix, participant_id, exclamation, form_serial, responses, comment) = result

        assert prefix == "XA"
        assert participant_id == test_participant_id
        assert exclamation is False
        assert responses == "AA1AB2"
        assert comment == test_comment


def test_context_switching():
    """Tests locale switching."""
    d = datetime(2010, 4, 12, 13, 46)

    MESSAGES_EN = [
        "INCOMING",
        "OUTGOING",
        "Checklist Not Found",
        "Delivered",
    ]
    MESSAGES_FR = [
        "ENTRANT",
        "SORTANT",
        "Formulaire non trouvé",
        "Envoyé",
    ]
    MESSAGES_AR = [
        "الوارد",
        "الصادر",
        "قائمة التحقق غير موجودة",
        "تم التسليم",
    ]

    assert babel.format_datetime(d) == "Apr 12, 2010, 1:46:00\u202fPM"
    assert babel.format_date(d) == "Apr 12, 2010"
    assert babel.format_time(d) == "1:46:00\u202fPM"

    with force_locale("en"):
        assert babel.format_datetime(d) == "Apr 12, 2010, 1:46:00\u202fPM"
        assert babel.format_date(d) == "Apr 12, 2010"
        assert babel.format_time(d) == "1:46:00\u202fPM"
        for orig_msg, trans_msg in zip(MESSAGES_EN, MESSAGES_EN):
            assert babel.gettext(orig_msg) == trans_msg

    with force_locale("fr"):
        assert babel.format_datetime(d) == "12 avr. 2010, 13:46:00"
        assert babel.format_date(d) == "12 avr. 2010"
        assert babel.format_time(d) == "13:46:00"
        for orig_msg, trans_msg in zip(MESSAGES_EN, MESSAGES_FR):
            assert babel.gettext(orig_msg) == trans_msg

    with force_locale("ar"):
        assert babel.format_datetime(d) == "12\u200f/04\u200f/2010، 1:46:00 م"
        assert babel.format_date(d) == "12\u200f/04\u200f/2010"
        assert babel.format_time(d) == "1:46:00 م"
        for orig_msg, trans_msg in zip(MESSAGES_EN, MESSAGES_AR):
            assert babel.gettext(orig_msg) == trans_msg


fixtures_path = DEFAULT_FIXTURES_PATH / "417efb586ef.sql"


def test_lookup_nonexistent_participant(app):
    """Test lookup of a non-existent participant."""
    fixtures.load_sql_fixture(fixtures_path)
    participant_id = "111111"
    phone_number = "111111"
    message = f"AV{participant_id}"

    assert lookup_participant(message, phone_number) is None
    event = services.events.fget_or_404(id=1)
    assert lookup_participant(message, phone_number, event) is None


def test_lookup_with_message(app):
    """Test participant lookup with message."""
    fixtures.load_sql_fixture(fixtures_path)
    participant_id = "403794"
    message = f"AV{participant_id}"
    phone_number = ""
    event1, event2, event3 = services.events.find().order_by("id").all()

    # participant doesn't exist in event1
    assert lookup_participant(message, phone_number, event1) is None

    # participant in event2...
    rv = lookup_participant(message, phone_number, event2)
    assert rv.participant_id == participant_id

    # ...is not the same as event3
    rv2 = lookup_participant(message, phone_number, event3)
    assert rv.participant_id == participant_id
    assert rv.id != rv2.id


def test_lookup_with_number(app):
    """Test lookup with phone number."""
    fixtures.load_sql_fixture(fixtures_path)
    participant_id = "111111"  # does not exist in any event
    phone_number = "7326767526"  # exists in event2 and event3
    message = f"AA{participant_id}"
    event1, event2, event3 = services.events.find().order_by("id").all()

    # participant doesn't exist in event1
    assert lookup_participant(message, phone_number, event1) is None

    # participant in event2...
    rv = lookup_participant(message, phone_number, event2)
    assert rv.phone_contacts[0].number == phone_number

    # ...is not the same as event3
    rv2 = lookup_participant(message, phone_number, event3)
    assert rv2.phone_contacts[0].number == phone_number
    assert rv.id != rv2.id
