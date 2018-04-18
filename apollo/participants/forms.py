# -*- coding: utf-8 -*-
from flask_babelex import lazy_gettext as _
from flask_wtf import FlaskForm
from wtforms import FileField, SelectField

from apollo.frontend.forms import _make_choices
from apollo.helpers import load_source_file


class ParticipantFileUploadForm(FlaskForm):
    spreadsheet = FileField(_('Data file'))


def make_import_mapping_form(import_file, participant_set):
    attributes = {}
    map_choices = _make_choices(participant_set.get_import_fields().items())

    data_frame = load_source_file(import_file)
    for index, column in enumerate(data_frame.columns):
        attributes[str(index)] = SelectField(column, choices=map_choices)

    return type('ParticipantImportMapForm', (FlaskForm,), attributes)
