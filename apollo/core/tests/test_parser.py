from unittest import TestCase
from core.documents import Form
from core.parser import (
    parse, PARSE_MULTIPLE_ENTRY, PARSE_OK, PARSE_UNEXPECTED_INPUT
)


class ParserTest(TestCase):
    checklist_form_schema = {
        'form_type': 'CHECKLIST',
        'groups': [{
            'fields': [{
                'name': 'AA',
                'represents_boolean': True
            }]
        }, {
            'fields': [{
                'name': 'AB',
            }, {
                'name': 'AC',
                'allows_multiple_values': True
            }]
        }]
    }
    incident_form_schema = {
        'form_type': 'INCIDENT',
        'groups': [{
            'fields': [{
                'name': 'A',
                'represents_boolean': True
            }, {
                'name': 'B',
                'represents_boolean': True
            }, {
                'name': 'C',
                'represents_boolean': True
            }]
        }]
    }

    def test_checklist_parse_unexpected(self):
        form = Form(**self.checklist_form_schema)
        sample_text = 'AAAB5AC12AD15'
        data, status = parse(form, sample_text)
        self.assertEqual(status, PARSE_UNEXPECTED_INPUT)

    def test_checklist_parse_multiple(self):
        # check what happens when differing values are entered
        form = Form(**self.checklist_form_schema)
        sample_text = 'AAAB5AC12AB6'
        data, status = parse(form, sample_text)
        self.assertEqual(status, PARSE_MULTIPLE_ENTRY)

        # check what happens when the same value is entered
        sample_text = 'AAAB5AC12AB5'
        data, status = parse(form, sample_text)
        self.assertEqual(status, PARSE_OK)

    def test_checklist_parse_success(self):
        form = Form(**self.checklist_form_schema)
        sample_text = 'AAAB5AC12'
        data, status = parse(form, sample_text)
        self.assertEqual(status, PARSE_OK)
        self.assertEqual(data.get('AA'), True)
        self.assertEqual(data.get('AB'), 5)
        self.assertEqual(sorted(data.get('AC')), [1, 2])

    def test_incident_parse_unexpected(self):
        form = Form(**self.incident_form_schema)
        sample_text = 'back'
        data, status = parse(form, sample_text)
        self.assertEqual(status, PARSE_UNEXPECTED_INPUT)

    def test_incident_parse_success(self):
        form = Form(**self.incident_form_schema)
        sample_text = 'cab'
        data, status = parse(form, sample_text)
        self.assertEqual(status, PARSE_OK)
        self.assertEqual(data.get('A'), True)
        self.assertEqual(data.get('B'), True)
        self.assertEqual(data.get('C'), True)
