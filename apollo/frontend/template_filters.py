import calendar
from collections import OrderedDict
import math
from babel.numbers import format_number
from flask import g
from flask.ext.babel import get_locale, lazy_gettext as _
import pandas as pd
from ..analyses.common import dataframe_analysis
from ..analyses.voting import proportion, variance


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


def percent_of(a, b):
    a_ = float(a if a else 0)
    b_ = float(b if b else 0)
    try:
        return (a_ / b_) * 100
    except ZeroDivisionError:
        return 0


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


def total_registered(
        dataframe, form, location_type, location, group='ALL', pure=False):
    try:
        if group == 'RURAL':
            df = dataframe.ix[
                dataframe.groupby(
                    [location_type, 'urban']).groups[(location, 0)]]
        elif group == 'URBAN':
            df = dataframe.ix[
                dataframe.groupby(
                    [location_type, 'urban']).groups[(location, 1)]]
        else:
            df = dataframe.ix[
                dataframe.groupby(location_type).groups[location]]

        c = df.ix[:, form.registered_voters_tag].sum()
        if pd.np.isnan(c):
            c = 0
        return number_format(int(c)) if not pure else int(c)
    except:
        return 0


def all_votes_total(
        dataframe, form, votes, location_type, location, group='ALL',
        pure=False):
    try:
        if group == 'RURAL':
            df = dataframe.ix[
                dataframe.groupby(
                    [location_type, 'urban']).groups[(location, 0)]]
        elif group == 'URBAN':
            df = dataframe.ix[
                dataframe.groupby(
                    [location_type, 'urban']).groups[(location, 1)]]
        else:
            df = dataframe.ix[
                dataframe.groupby(location_type).groups[location]]

        df = df[eval(' | '.join(['(df["{}"] >= 0)'.format(v) for v in votes]))]

        invalid_votes = form.invalid_votes_tag
        c = df.ix[:, votes + [invalid_votes]
                  if invalid_votes else []].sum().sum(axis=1)
        if pd.np.isnan(c):
            c = 0
        return number_format(int(c)) if not pure else int(c)
    except:
        return 0


def all_votes_total_pct(
    dataframe, form, votes, location_type, location, group='ALL'
):
    denom = float(total_registered(dataframe,
                  form, location_type, location, group, pure=True))
    num = float(all_votes_total(dataframe,
                form, votes, location_type, location, group, pure=True))
    try:
        f = round((num / denom * 100.0), 2)
        return '%.2f' % f if f % 1 else '%d' % f
    except ZeroDivisionError:
        return 0


def all_votes_total_margin_of_error(
    dataframe, form, votes, location_type, location, group='ALL',
    cv=196.0
):
    try:
        if group == 'RURAL':
            df = dataframe.ix[
                dataframe.groupby(
                    [location_type, 'urban']).groups[(location, 0)]]
        elif group == 'URBAN':
            df = dataframe.ix[
                dataframe.groupby(
                    [location_type, 'urban']).groups[(location, 1)]]
        else:
            df = dataframe.ix[
                dataframe.groupby(location_type).groups[location]]

        df = df[eval(' | '.join(['(df["{}"] >= 0)'.format(v) for v in votes]))]

        invalid_votes = form.invalid_votes_tag
        all_votes = votes + [invalid_votes] if invalid_votes else []
        total_registered = [form.registered_voters_tag]

        v = round(
            abs(math.sqrt(
                variance(df, total_registered, all_votes)) * cv), 2)
        if pd.np.isnan(v) or pd.np.isinf(v):
            v = 0
        return '%.2f' % v if v % 1 else '%d' % v
    except:
        return 0


def valid_votes_total(dataframe, votes, location_type, location, group='ALL'):
    try:
        if group == 'RURAL':
            df = dataframe.ix[
                dataframe.groupby(
                    [location_type, 'urban']).groups[(location, 0)]]
        elif group == 'URBAN':
            df = dataframe.ix[
                dataframe.groupby(
                    [location_type, 'urban']).groups[(location, 1)]]
        else:
            df = dataframe.ix[
                dataframe.groupby(location_type).groups[location]]

        df = df[eval(' | '.join(['(df["{}"] >= 0)'.format(v) for v in votes]))]

        c = df.ix[:, votes].sum().sum(axis=1)
        if pd.np.isnan(c):
            c = 0
        return number_format(int(c))
    except:
        return 0


def vote_count(dataframe, votes, vote, location_type, location, group='ALL'):
    try:
        if group == 'RURAL':
            df = dataframe.ix[
                dataframe.groupby(
                    [location_type, 'urban']).groups[(location, 0)]]
        elif group == 'URBAN':
            df = dataframe.ix[
                dataframe.groupby(
                    [location_type, 'urban']).groups[(location, 1)]]
        else:
            df = dataframe.ix[
                dataframe.groupby(location_type).groups[location]]

        df = df[eval(' | '.join(['(df["{}"] >= 0)'.format(v) for v in votes]))]

        c = df[vote].sum()
        if pd.np.isnan(c):
            c = 0
        return number_format(int(c))
    except:
        return 0


def rejected_count(dataframe, form, location_type, location, group='ALL'):
    votes = form.party_mappings.values()

    try:
        if group == 'RURAL':
            df = dataframe.ix[
                dataframe.groupby(
                    [location_type, 'urban']).groups[(location, 0)]]
        elif group == 'URBAN':
            df = dataframe.ix[
                dataframe.groupby(
                    [location_type, 'urban']).groups[(location, 1)]]
        else:
            df = dataframe.ix[
                dataframe.groupby(location_type).groups[location]]

        df = df[eval(' | '.join(['(df["{}"] >= 0)'.format(v) for v in votes]))]
        rejected = form.invalid_votes_tag

        if rejected:
            c = df[rejected].sum()
        else:
            c = 0

        if pd.np.isnan(c):
            c = 0
        return number_format(int(c))
    except:
        return 0


def vote_proportion(
    dataframe, form, votes, vote, location_type, location, group='ALL'
):
    try:
        if group == 'RURAL':
            df = dataframe.ix[
                dataframe.groupby(
                    [location_type, 'urban']).groups[(location, 0)]]
        elif group == 'URBAN':
            df = dataframe.ix[
                dataframe.groupby(
                    [location_type, 'urban']).groups[(location, 1)]]
        else:
            df = dataframe.ix[
                dataframe.groupby(location_type).groups[location]]

        df = df[eval(' | '.join(['(df["{}"] >= 0)'.format(v) for v in votes]))]

        if g.deployment.include_rejected_in_votes and form.invalid_votes_tag:
            votes += [form.invalid_votes_tag]

        p = round(abs(proportion(df, votes, [vote]) * 100.0), 2)
        if pd.np.isnan(p):
            p = 0
        return '%.2f' % p if p % 1 else '%d' % p
    except:
        return 0


def rejected_proportion(dataframe, form, location_type, location, group='ALL'):
    votes = form.party_mappings.values()

    try:
        if group == 'RURAL':
            df = dataframe.ix[
                dataframe.groupby(
                    [location_type, 'urban']).groups[(location, 0)]]
        elif group == 'URBAN':
            df = dataframe.ix[
                dataframe.groupby(
                    [location_type, 'urban']).groups[(location, 1)]]
        else:
            df = dataframe.ix[
                dataframe.groupby(location_type).groups[location]]

        df = df[eval(' | '.join(['(df["{}"] >= 0)'.format(v) for v in votes]))]
        rejected = form.invalid_votes_tag

        if rejected:
            r = round(
                abs(proportion(df, votes + [rejected], [rejected]) * 100.0), 2)
        else:
            r = 0

        if pd.np.isnan(r) or pd.np.isinf(r):
            r = 0
        return '%.2f' % r if r % 1 else '%d' % r
    except:
        return 0


def vote_margin_of_error(
    dataframe, form, votes, vote, location_type, location, group='ALL',
    cv=196.0
):
    try:
        if group == 'RURAL':
            df = dataframe.ix[
                dataframe.groupby(
                    [location_type, 'urban']).groups[(location, 0)]]
        elif group == 'URBAN':
            df = dataframe.ix[
                dataframe.groupby(
                    [location_type, 'urban']).groups[(location, 1)]]
        else:
            df = dataframe.ix[
                dataframe.groupby(location_type).groups[location]]

        df = df[eval(' | '.join(['(df["{}"] >= 0)'.format(v) for v in votes]))]

        if g.deployment.include_rejected_in_votes and form.invalid_votes_tag:
            votes += [form.invalid_votes_tag]

        v = round(abs(math.sqrt(variance(df, votes, [vote])) * cv), 2)
        if pd.np.isnan(v) or pd.np.isinf(v):
            v = 0
        return '%.2f' % v if v % 1 else '%d' % v
    except:
        return 0


def rejected_margin_of_error(
    dataframe, form, location_type, location, group='ALL', cv=196.0
):
    votes = form.party_mappings.values()

    try:
        if group == 'RURAL':
            df = dataframe.ix[
                dataframe.groupby(
                    [location_type, 'urban']).groups[(location, 0)]]
        elif group == 'URBAN':
            df = dataframe.ix[
                dataframe.groupby(
                    [location_type, 'urban']).groups[(location, 1)]]
        else:
            df = dataframe.ix[
                dataframe.groupby(location_type).groups[location]]

        df = df[eval(' | '.join(['(df["{}"] >= 0)'.format(v) for v in votes]))]
        rejected = form.invalid_votes_tag

        if rejected:
            r = round(
                abs(math.sqrt(
                    variance(df, votes + [rejected], [rejected])) * cv), 2)
        else:
            r = 0

        if pd.np.isnan(r) or pd.np.isinf(r):
            r = 0
        return '%.2f' % r if r % 1 else '%d' % r
    except:
        return 0


def reported(
        dataframe, votes, location_type, location, group='ALL', pure=False):
    try:
        if group == 'RURAL':
            df = dataframe.ix[dataframe.groupby(
                [location_type, 'urban']
            ).groups[(location, 0)]]
        elif group == 'URBAN':
            df = dataframe.ix[dataframe.groupby(
                [location_type, 'urban']
            ).groups[(location, 1)]]
        else:
            df = dataframe.ix[dataframe.groupby(
                location_type).groups[location]]

        rp = df[
            eval(' | '.join(['(df["{}"] >= 0)'.format(v) for v in votes]))
            ].shape[0]
        return int(rp) if pure else number_format(int(rp))
    except:
        return 0


def missing(
        dataframe, votes, location_type, location, group='ALL', pure=False):
    try:
        if group == 'RURAL':
            df = dataframe.ix[dataframe.groupby(
                [location_type, 'urban']
            ).groups[(location, 0)]]
        elif group == 'URBAN':
            df = dataframe.ix[
                dataframe.groupby(
                    [location_type, 'urban']).groups[(location, 1)]]
        else:
            df = dataframe.ix[
                dataframe.groupby(location_type).groups[location]]

        m = df[
            eval(' & '.join(
                ['(df["{}"].isnull())'.format(v) for v in votes]))].shape[0]
        return int(m) if pure else number_format(int(m))
    except:
        return 0


def reported_pct(dataframe, votes, location_type, location, group='ALL'):
    m = float(
        missing(dataframe, votes, location_type, location, group, pure=True))
    r = float(
        reported(dataframe, votes, location_type, location, group, pure=True))
    try:
        f = round((r / (m + r) * 100.0), 2)
        return '%.2f' % f if f % 1 else '%d' % f
    except ZeroDivisionError:
        return 0


def missing_pct(dataframe, votes, location_type, location, group='ALL'):
    m = float(
        missing(dataframe, votes, location_type, location, group, pure=True))
    r = float(
        reported(dataframe, votes, location_type, location, group, pure=True))
    try:
        f = round((m / (m + r) * 100.0), 2)
        return '%.2f' % f if f % 1 else '%d' % f
    except ZeroDivisionError:
        return 0
