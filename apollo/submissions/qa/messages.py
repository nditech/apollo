# -*- coding: utf-8 -*-
import enum

from flask_babelex import gettext as _


class FlagCause(enum.IntEnum):
    EMPTY_EXPRESSION = 1
    MALFORMED_EXPRESSION = 2
    MISSING_VARIABLE = 3
    MULTISELECT_VARIABLE = 4


FLAG_MESSAGES = {
    FlagCause.EMPTY_EXPRESSION: _('Empty QA expression'),
    FlagCause.MALFORMED_EXPRESSION: _('Malformed QA expression'),
    FlagCause.MISSING_VARIABLE: _('Nonexistent question code'),
    FlagCause.MULTISELECT_VARIABLE: _('Multple choice question used'),
}
