# -*- coding: utf-8 -*-
from flask_babelex import lazy_gettext as _
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms.fields import StringField
from wtforms.validators import InputRequired
from wtforms.widgets import HiddenInput


class SampleForm(FlaskForm):
    '''Sample creation form'''
    name = StringField(_('Name'), validators=[InputRequired()])
    location_data = StringField(
        _('Locations'), widget=HiddenInput())


class AdminDivisionImportForm(FlaskForm):
    '''Form for processing admin division imports'''
    import_file = FileField(_('Import file'), validators=[InputRequired()])
