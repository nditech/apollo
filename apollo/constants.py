# -*- coding: utf-8 -*-
import codecs
from operator import itemgetter

from apollo.settings import LANGUAGES

BOM_UTF8_BYTES = codecs.BOM_UTF8
BOM_UTF8_STR = str(BOM_UTF8_BYTES, 'utf-8')

LANGUAGE_CHOICES = [(None, '')] + \
    sorted(LANGUAGES.items(), key=itemgetter(0))
