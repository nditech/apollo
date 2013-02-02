from .models import Form, Activity


def generate_dashboard_summary(submission_queryset):
    summary = []

    # filter out and only select checklists to be filled by observers
    try:
        form = submission_queryset.filter(form__type="CHECKLIST")[0].form
        for group in form.groups.all():
            complete = submission_queryset.filter(form__type="CHECKLIST").exclude(observer=None).is_complete(group).count()
            missing = submission_queryset.filter(form__type="CHECKLIST").exclude(observer=None).is_missing(group).count()
            partial = submission_queryset.filter(form__type="CHECKLIST").exclude(observer=None).is_partial(group).count()

            group_summary = {'name': group.name, 'complete': complete, 'missing': missing, 'partial': partial}

            summary.append(group_summary)
    except (AttributeError, IndexError):
        # perhaps we didn't actually get a Form object
        pass

    return summary
