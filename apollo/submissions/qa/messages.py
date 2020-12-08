# -*- coding: utf-8 -*-
import enum


class FlagCause(enum.IntEnum):
    EMPTY_EXPRESSION = 1
    MALFORMED_EXPRESSION = 2
    MISSING_VARIABLE = 3
    MULTISELECT_VARIABLE = 4
