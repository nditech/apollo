# -*- coding: utf-8 -*-
from flask_babelex import lazy_gettext as _
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileRequired
from wtforms import FileField, SelectField
from wtforms.validators import InputRequired

from apollo import models, services
from apollo.frontend.forms import _make_choices

SPREADSHEET_FORMATS = ['csv', 'ods', 'tsv', 'xls', 'xlsx']


def participant_upload_form_factory(deployment):
    location_sets = services.location_sets.find(
        deployment=deployment
    ).with_entities(models.LocationSet.id, models.LocationSet.name)

    class ParticipantFileUploadForm(FlaskForm):
        location_set = SelectField(
            _('Location set'),
            choices=_make_choices(location_sets, _('Select one')),
            validators=[InputRequired()])
        spreadsheet = FileField(
            _('Data file'),
            validators=[FileAllowed(SPREADSHEET_FORMATS), FileRequired()])

    return ParticipantFileUploadForm
