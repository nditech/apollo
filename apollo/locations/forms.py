# -*- coding: utf-8 -*-
from flask_babelex import lazy_gettext as _
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms.fields import SelectField, StringField
from wtforms.validators import InputRequired
from wtforms.widgets import HiddenInput

from apollo.frontend.forms import _make_choices
from apollo.helpers import load_source_file


class SampleForm(FlaskForm):
    '''Sample creation form'''
    name = StringField(_('Name'), validators=[InputRequired()])
    location_data = StringField(
        _('Locations'), widget=HiddenInput())


class AdminDivisionImportForm(FlaskForm):
    '''Form for processing admin division imports'''
    import_file = FileField(_('Import file'), validators=[InputRequired()])


def make_import_mapping_form(import_file, location_set):
    attributes = {}
    map_choices = _make_choices(location_set.get_import_fields().items())

    data_frame = load_source_file(import_file)
    for index, column in enumerate(data_frame.columns):
        attributes[str(index)] = SelectField(column, choices=map_choices)

    return type('LocationImportMapForm', (FlaskForm,), attributes)
