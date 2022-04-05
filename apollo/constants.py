# -*- coding: utf-8 -*-
import codecs
from operator import itemgetter

from flask_babelex import lazy_gettext as _

from apollo.settings import LANGUAGES

BOM_UTF8_BYTES = codecs.BOM_UTF8
BOM_UTF8_STR = str(BOM_UTF8_BYTES, 'utf-8')

LANGUAGE_CHOICES = [('', _('(None)'))] + \
    sorted(LANGUAGES.items(), key=itemgetter(0))

CSV_MIMETYPES = [
    "text/csv",
    "application/csv",
    "text/x-csv",
    "application/x-csv",
    "text/comma-separated-values",
    "text/x-comma-separated-values",
]

EXCEL_MIMETYPES = [
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
]
