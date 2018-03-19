# -*- coding: utf-8 -*-
from flask_babelex import lazy_gettext as _
from flask_wtf import FlaskForm
from wtforms import FileField


class ParticipantFileUploadForm(FlaskForm):
    spreadsheet = FileField(_('Data file'))
