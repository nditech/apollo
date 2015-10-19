import calendar
from collections import OrderedDict
import re
from babel.numbers import format_number
from flask.ext.babel import get_locale, lazy_gettext as _
import pandas as pd
from apollo.process_analysis.common import (
    dataframe_analysis, multiselect_dataframe_analysis)


def _clean(fieldname):
    '''Returns a sanitized fieldname'''
    return re.sub(r'[^A-Z]', '', fieldname, re.I)


def checklist_question_summary(form, field, location, dataframe):
    stats = {'urban': {}}
    if field.options:
        stats['type'] = 'discrete'
        stats['options'] = OrderedDict(
            sorted(field.options.items(), key=lambda x: x[1])
        )
    else:
        stats['type'] = 'continuous'

    if field.allows_multiple_values:
        stats.update(multiselect_dataframe_analysis(
            dataframe, field.name, sorted(field.options.values())))
    else:
        stats.update(dataframe_analysis(stats['type'], dataframe, field.name))

    try:
        for name, grp in dataframe.groupby('urban'):
            stats['urban']['Urban' if name else 'Rural'] = dataframe_analysis(
                stats['type'], grp, field.name)
    except KeyError:
        pass

    return {
        'form': form, 'location': location, 'field': field, 'stats': stats
    }


def get_location_for_type(submission, location_type, display_type=False):
    locations = [loc for loc in (
        list(submission.location.ancestors_ref) +
        [submission.location]
    )
        if loc.location_type == location_type.name]

    if display_type:
        return u'{} &middot; <em class="muted">{}</em>'.format(
            locations[0].name, locations[0].location_type
        ) if locations else u''
    else:
        return locations[0].name if locations else u''


def gen_page_list(pager, window_size=10):
    '''Utility function for generating a list of pages numbers from a pager.
    Shamelessly ripped from django-bootstrap-pagination.'''
    if window_size > pager.pages:
        window_size = pager.pages
    window_size -= 1
    start = max(pager.page - (window_size / 2), 1)
    end = min(pager.page + (window_size / 2), pager.pages)

    diff = end - start
    if diff < window_size:
        shift = window_size - diff
        if (start - shift) > 0:
            start -= shift
        else:
            end += shift
    return range(start, end + 1)


def percent_of(a, b, default=None):
    a_ = float(a if a else 0)
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
