# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm
from wtforms.fields import HiddenField
from wtforms.validators import input_required

from .participants.forms import * # noqa


class UserImportForm(FlaskForm):
    payload = HiddenField(validators=[input_required()])
