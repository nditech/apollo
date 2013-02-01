from .models import Form


def generate_dashboard_summary(submission_queryset, form):
    summary = []

    # filter out and only select checklists to be filled by observers
    for group in form.groups.all():
        complete = submission_queryset.exclude(observer=None).is_complete(group).count()
        missing = submission_queryset.exclude(observer=None).is_missing(group).count()
        partial = submission_queryset.exclude(observer=None).is_partial(group).count()

        group_summary = {group.name: {'complete': complete, 'missing': missing, 'partial': partial}}

        summary.append(group_summary)

    return summary
