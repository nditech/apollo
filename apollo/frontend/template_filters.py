# -*- coding: utf-8 -*-
import calendar
from collections import OrderedDict
import re

from babel.numbers import format_number
from flask import Markup
from flask_babelex import get_locale, lazy_gettext as _
import pandas as pd

from apollo.process_analysis.common import (
    dataframe_analysis, multiselect_dataframe_analysis)
from apollo.submissions.models import QUALITY_STATUSES
from apollo.submissions.qa.query_builder import get_inline_qa_status


def _clean(fieldname):
    '''Returns a sanitized fieldname'''
    return re.sub(r'[^A-Z]', '', fieldname, re.I)


def checklist_question_summary(form, field, location, dataframe):
    field_type = field.get('type')
    stats = {'urban': {}}
    if field_type in ('select', 'multiselect'):
        stats['type'] = 'discrete'
        stats['options'] = OrderedDict(
            sorted(field.get('options').items(), key=lambda x: x[1])
        )
    else:
        stats['type'] = 'continuous'

    if field_type == 'multiselect':
        stats.update(multiselect_dataframe_analysis(
            dataframe, field['tag'], sorted(field.get('options').values())))
    else:
        stats.update(dataframe_analysis(stats['type'], dataframe, field['tag']))

    try:
        for name, grp in dataframe.groupby('urban'):
            if field_type == 'multiselect':
                stats['urban']['Urban' if name else 'Rural'] = \
                    multiselect_dataframe_analysis(
                        grp, field['tag'], sorted(field.get('options').values()))
            else:
                stats['urban']['Urban' if name else 'Rural'] = \
                    dataframe_analysis(stats['type'], grp, field['tag'])
    except KeyError:
        pass

    return {
        'form': form, 'location': location, 'field': field, 'stats': stats
    }


def get_location_for_type(submission, location_type, display_type=False):
    location = submission.location.make_path().get(
        location_type.name)

    if display_type:
        return Markup('{} &middot; <em class="muted">{}</em>').format(
            location, location_type.name
        ) if location else ''
    else:
        return location if location else ''


def gen_page_list(pager, window_size=10):
    '''Utility function for generating a list of pages numbers from a pager.
    Shamelessly ripped from django-bootstrap-pagination.'''
    if window_size > pager.pages:
        window_size = pager.pages
    window_size -= 1
    start = max(pager.page - (window_size // 2), 1)
    end = min(pager.page + (window_size // 2), pager.pages)

    diff = end - start
    if diff < window_size:
        shift = window_size - diff
        if (start - shift) > 0:
            start -= shift
        else:
            end += shift
    return list(range(start, end + 1))


def percent_of(a, b, default=None):
    a_ = float(a if (a and not pd.np.isinf(a)) else 0)
    b_ = float(b if b else 0)
    try:
        return (a_ / b_) * 100
    except ZeroDivisionError:
        return default or 0


def mean_filter(value):
    if pd.isnull(value):
        return _('N/A')
    else:
        return int(round(value))


def mkunixtimestamp(dt):
    '''Creates a unix timestamp from a datetime.'''
    return calendar.timegm(dt.utctimetuple())


def number_format(number):
    locale = get_locale()
    if locale is None:
        return format_number(number)
    return format_number(number, locale)


def reverse_dict(d):
    return {v: k for k, v in list(d.items())}


def qa_status(submission, check):
    result, _ = get_inline_qa_status(submission, check)
    if result is True:
        return QUALITY_STATUSES['OK']
    elif result is False:
        return QUALITY_STATUSES['FLAGGED']
    else:
        return None
