from numpy import *
from core.models import *


def analyze_tag(queryset, tag):
    '''Analyzes a given tag, and returns statistics for the supplied
    queryset'''
    # get the type of field associated with the tag
    # TODO: confirm that this queryset is indeed, for just one form
    form = queryset[0].form
    field = FormField.objects.get(group__form=form, tag=tag)

    options = field.options.all()

    if options:
        # tag has options, so just get counts of each tag that appears
        stats = {}

        for submission in queryset:
            value = submission.data[tag]
            stats[value] = stats.get(value, 0) + 1

        return stats

    else:
        dataset = array([int(submission.data[tag]) for submission in queryset])

        # supposed to return dataset.min(), dataset.max(), dataset.average() 