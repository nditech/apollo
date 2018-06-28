# -*- coding: utf-8 -*-
from flask_babelex import lazy_gettext as _
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from slugify import slugify_unicode
from wtforms import SelectField

from apollo.frontend.forms import _make_choices
from apollo.helpers import load_source_file


class ParticipantFileUploadForm(FlaskForm):
    spreadsheet = FileField(
        _('Data file'), validators=[FileRequired(_('Please upload a file'))]
    )


def _validate_required_fields(form):
    # call superclass method
    rv = FlaskForm.validate(form)

    mapped_form_values = form.data.values()
    errors = []

    if 'id' not in mapped_form_values:
        errors.append(str(_('Participant ID was not mapped')))
        rv = False

    form.errors['__validate__'] = errors

    return rv


def make_import_mapping_form(import_file, participant_set):
    attributes = {'validate': _validate_required_fields}
    map_choices = _make_choices(participant_set.get_import_fields().items())

    data_frame = load_source_file(import_file)
    for column in data_frame.columns:
        attributes[slugify_unicode(column)] = SelectField(
            column, choices=map_choices)

    return type('ParticipantImportMapForm', (FlaskForm,), attributes)
