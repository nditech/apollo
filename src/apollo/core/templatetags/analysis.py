# -*- coding: utf-8 -*-
from collections import OrderedDict
from django import template
from django.utils.formats import number_format
import pandas as pd
import math
from analyses.voting import proportion, variance


register = template.Library()


def dataframe_analysis(type, dataframe, col):
    if type == 'discrete':
        try:
            result = {'value_counts': dict(getattr(dataframe, col).value_counts()),
                'value_counts_sum': getattr(dataframe, col).value_counts().sum()}
        except AttributeError:
            result = {'value_counts': pd.np.nan, 'value_counts_sum': 0}
    else:
        try:
            result = {'mean': getattr(dataframe, col).mean()}
        except AttributeError:
            result = {'mean': pd.np.nan}

    try:
        result['count'] = getattr(dataframe, col).count()
        result['size'] = getattr(dataframe, col).size
        result['diff'] = result['size'] - result['count']
    except AttributeError:
        result.update({'count': 0, 'size': 0, 'diff': 0})

    return result


@register.inclusion_tag('core/checklist_question_summary.html')
def checklist_question_summary(form, field, location, dataframe):
    stats = {'urban': {}}
    if field.options.exists():
        stats['type'] = 'discrete'
        stats['options'] = OrderedDict(field.options.order_by('option').values_list('description', 'option'))
    else:
        stats['type'] = 'continuous'

    stats.update(dataframe_analysis(stats['type'], dataframe, field.tag))

    try:
        for name, grp in dataframe.groupby('urban'):
            stats['urban']['Urban' if name else 'Rural'] = dataframe_analysis(stats['type'], grp, field.tag)
    except KeyError:
        pass

    return {'form': form, 'location': location,
        'field': field, 'stats': stats}


@register.filter
def default_if_nan(value, default):
    if value == pd.np.nan:
        return default
    else:
        return value


@register.simple_tag
def votes_total(dataframe, votes, location_type, location, group='ALL'):
    try:
        if group == 'RURAL':
            df = dataframe.ix[dataframe.groupby([location_type, 'urban']).groups[(location, 0)]]
        elif group == 'URBAN':
            df = dataframe.ix[dataframe.groupby([location_type, 'urban']).groups[(location, 1)]]
        else:
            df = dataframe.ix[dataframe.groupby(location_type).groups[location]]

        df = df[eval(' | '.join(['(df.{} >= 0)'.format(v) for v in votes]))]

        c = df.ix[:, votes].sum(skipna=True).sum(axis=1, skipna=True)
        if pd.np.isnan(c):
            c = 0
        return number_format(int(c), force_grouping=True)
    except:
        return 0


@register.simple_tag
def vote_count(dataframe, votes, vote, location_type, location, group='ALL'):
    try:
        if group == 'RURAL':
            df = dataframe.ix[dataframe.groupby([location_type, 'urban']).groups[(location, 0)]]
        elif group == 'URBAN':
            df = dataframe.ix[dataframe.groupby([location_type, 'urban']).groups[(location, 1)]]
        else:
            df = dataframe.ix[dataframe.groupby(location_type).groups[location]]

        df = df[eval(' | '.join(['(df.{} >= 0)'.format(v) for v in votes]))]

        c = df[vote].sum()
        if pd.np.isnan(c):
            c = 0
        return number_format(int(c), force_grouping=True)
    except:
        return 0


@register.simple_tag
def rejected_count(form, dataframe, location_type, location, group='ALL'):
    votes = form.votes()

    try:
        if group == 'RURAL':
            df = dataframe.ix[dataframe.groupby([location_type, 'urban']).groups[(location, 0)]]
        elif group == 'URBAN':
            df = dataframe.ix[dataframe.groupby([location_type, 'urban']).groups[(location, 1)]]
        else:
            df = dataframe.ix[dataframe.groupby(location_type).groups[location]]

        df = df[eval(' | '.join(['(df.{} >= 0)'.format(v) for v in votes]))]
        rejected = form.options.get('votes_invalid', None)

        if rejected:
            c = df[rejected].sum()
        else:
            c = 0
        
        if pd.np.isnan(c):
            c = 0
        return number_format(int(c), force_grouping=True)
    except:
        return 0


@register.simple_tag
def vote_proportion(dataframe, votes, vote, location_type, location, group='ALL'):
    try:
        if group == 'RURAL':
            df = dataframe.ix[dataframe.groupby([location_type, 'urban']).groups[(location, 0)]]
        elif group == 'URBAN':
            df = dataframe.ix[dataframe.groupby([location_type, 'urban']).groups[(location, 1)]]
        else:
            df = dataframe.ix[dataframe.groupby(location_type).groups[location]]

        df = df[eval(' | '.join(['(df.{} >= 0)'.format(v) for v in votes]))]

        p = round(abs(proportion(df, votes, vote) * 100.0), 2)
        if pd.np.isnan(p):
            p = 0
        return '%.2f' % p if p % 1 else '%d' % p
    except:
        return 0


@register.simple_tag
def rejected_proportion(form, dataframe, location_type, location, group='ALL'):
    votes = form.votes()

    try:
        if group == 'RURAL':
            df = dataframe.ix[dataframe.groupby([location_type, 'urban']).groups[(location, 0)]]
        elif group == 'URBAN':
            df = dataframe.ix[dataframe.groupby([location_type, 'urban']).groups[(location, 1)]]
        else:
            df = dataframe.ix[dataframe.groupby(location_type).groups[location]]

        df = df[eval(' | '.join(['(df.{} >= 0)'.format(v) for v in votes]))]
        rejected = form.options.get('votes_invalid', None)

        if rejected:
            r = round(abs(proportion(df, votes + [rejected], rejected) * 100.0), 2)
        else:
            r = 0

        if pd.np.isnan(r) or pd.np.isinf(r):
            r = 0
        return '%.2f' % r if r % 1 else '%d' % r
    except:
        return 0


@register.simple_tag
def vote_margin_of_error(dataframe, votes, vote, location_type, location, group='ALL'):
    try:
        if group == 'RURAL':
            df = dataframe.ix[dataframe.groupby([location_type, 'urban']).groups[(location, 0)]]
        elif group == 'URBAN':
            df = dataframe.ix[dataframe.groupby([location_type, 'urban']).groups[(location, 1)]]
        else:
            df = dataframe.ix[dataframe.groupby(location_type).groups[location]]

        df = df[eval(' | '.join(['(df.{} >= 0)'.format(v) for v in votes]))]

        v = round(abs(math.sqrt(variance(df, votes, vote)) * 196.0), 2)
        if pd.np.isnan(v) or pd.np.isinf(v):
            v = 0
        return '%.2f' % v if v % 1 else '%d' % v
    except:
        return 0


@register.simple_tag
def rejected_margin_of_error(form, dataframe, location_type, location, group='ALL'):
    votes = form.votes()

    try:
        if group == 'RURAL':
            df = dataframe.ix[dataframe.groupby([location_type, 'urban']).groups[(location, 0)]]
        elif group == 'URBAN':
            df = dataframe.ix[dataframe.groupby([location_type, 'urban']).groups[(location, 1)]]
        else:
            df = dataframe.ix[dataframe.groupby(location_type).groups[location]]

        df = df[eval(' | '.join(['(df.{} >= 0)'.format(v) for v in votes]))]
        rejected = form.options.get('votes_invalid', None)

        if rejected:
            r = round(abs(math.sqrt(variance(df, votes + [rejected], rejected)) * 196.0), 2)
        else:
            r = 0

        if pd.np.isnan(r) or pd.np.isinf(r):
            r = 0
        return '%.2f' % r if r % 1 else '%d' % r
    except:
        return 0


@register.simple_tag
def reported(dataframe, votes, location_type, location, group='ALL', pure=False):
    try:
        if group == 'RURAL':
            df = dataframe.ix[dataframe.groupby([location_type, 'urban']).groups[(location, 0)]]
        elif group == 'URBAN':
            df = dataframe.ix[dataframe.groupby([location_type, 'urban']).groups[(location, 1)]]
        else:
            df = dataframe.ix[dataframe.groupby(location_type).groups[location]]
            
        rp = df[eval(' | '.join(['(df.{} >= 0)'.format(v) for v in votes]))].shape[0]
        return int(rp) if pure else number_format(int(rp), force_grouping=True)
    except:
        return 0


@register.simple_tag
def missing(dataframe, votes, location_type, location, group='ALL', pure=False):
    try:
        if group == 'RURAL':
            df = dataframe.ix[dataframe.groupby([location_type, 'urban']).groups[(location, 0)]]
        elif group == 'URBAN':
            df = dataframe.ix[dataframe.groupby([location_type, 'urban']).groups[(location, 1)]]
        else:
            df = dataframe.ix[dataframe.groupby(location_type).groups[location]]
            
        m = df[eval(' & '.join(['(df.{}.isnull())'.format(v) for v in votes]))].shape[0]
        return int(m) if pure else number_format(int(m), force_grouping=True)
    except:
        return 0


@register.simple_tag
def reported_pct(dataframe, votes, location_type, location, group='ALL'):
    m = float(missing(dataframe, votes, location_type, location, group, pure=True))
    r = float(reported(dataframe, votes, location_type, location, group, pure=True))
    try:
        f = round((r / (m+r) * 100.0), 2)
        return '%.2f' % f if f % 1 else '%d' % f
    except ZeroDivisionError:
        return 0


@register.simple_tag
def missing_pct(dataframe, votes, location_type, location, group='ALL'):
    m = float(missing(dataframe, votes, location_type, location, group, pure=True))
    r = float(reported(dataframe, votes, location_type, location, group, pure=True))
    try:
        f = round((m / (m+r) * 100.0), 2)
        return '%.2f' % f if f % 1 else '%d' % f
    except ZeroDivisionError:
        return 0
