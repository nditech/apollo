from .models import Form


def generate_dashboard_summary(form_id, submission_queryset):
    try:
        form = Form.objects.get(pk=form_id)
    except Form.DoesNotExist:
        return {}

    summary = []

    for group in form.groups.all():
        complete = submission_queryset.filter(observer=None).is_complete(group).count()
        missing = submission_queryset.filter(observer=None).is_missing(group).count()
        partial = submission_queryset.filter(observer=None).is_partial(group).count()

        group_summary = {group.name.lower(): {'complete': complete, 'missing': missing, 'partial': partial}}

        summary.append(group_summary)

    return summary
