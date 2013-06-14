# -*- coding: utf-8 -*-
from collections import OrderedDict
from django import template
import pandas as pd


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
            result = {'mean': getattr(dataframe, col).mean().round()}
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
