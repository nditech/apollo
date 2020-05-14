# -*- coding: utf-8 -*-
import calendar
import re

from babel.numbers import format_number
from datetime import date, datetime
from flask import Markup
from flask_babelex import get_locale, lazy_gettext as _
from geoalchemy2.shape import to_shape
import pandas as pd

from apollo.process_analysis.common import generate_field_stats
from apollo.submissions.models import QUALITY_STATUSES
from apollo.submissions.qa.query_builder import get_inline_qa_status


def _clean(fieldname):
    '''Returns a sanitized fieldname'''
    return re.sub(r'[^A-Z]', '', fieldname, re.I)


def checklist_question_summary(form, field, location, dataframe):
    stats = {'urban': {}}
    stats.update(generate_field_stats(field, dataframe))

    try:
        for name, grp in dataframe.groupby('urban'):
            stats['urban']['Urban' if name else 'Rural'] = \
                    generate_field_stats(field, grp)
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
    if type(dt) == datetime:
        return calendar.timegm(dt.utctimetuple())
    elif type(dt) == date:
        return calendar.timegm(datetime.combine(
            dt, datetime.min.time()).utctimetuple())
    else:
        return calendar.timegm(datetime.min.utctimetuple())


def number_format(number):
    locale = get_locale()
    if locale is None:
        return format_number(number)
    return format_number(number, locale)


def reverse_dict(d):
    return {v: k for k, v in list(d.items())}


def qa_status(submission, check):
    result, tags = get_inline_qa_status(submission, check)
    verified_fields = submission.verified_fields or set()
    if result is True and not tags.issubset(verified_fields):
        return QUALITY_STATUSES['FLAGGED']
    elif result is True and tags.issubset(verified_fields):
        return QUALITY_STATUSES['VERIFIED']
    elif result is False:
        return QUALITY_STATUSES['OK']
    else:
        return None


def longitude(geom):
    return to_shape(geom).x


def latitude(geom):
    return to_shape(geom).y
