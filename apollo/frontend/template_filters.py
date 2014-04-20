from collections import OrderedDict
from ..analyses.common import dataframe_analysis


def checklist_question_summary(form, field, location, dataframe):
    stats = {'urban': {}}
    if field.options:
        stats['type'] = 'discrete'
        stats['options'] = OrderedDict(
            sorted(field.options.items(), key=lambda x: x[1])
        )
    else:
        stats['type'] = 'continuous'

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


def percent_of(a, b):
    a_ = float(a if a else 0)
    b_ = float(b if b else 0)
    try:
        return (a_ / b_) * 100
    except ZeroDivisionError:
        return 0
