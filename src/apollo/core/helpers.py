from .models import Form, Location, Submission


def generate_dashboard_summary(form_id, location_id):
    try:
        form = Form.objects.get(pk=form_id)
        location = Location.objects.get(pk=location_id)
    except Form.DoesNotExist:
        return {}
    except Location.DoesNotExist:
        return {}

    summary = {}

    for group in form.groups.all():
        complete = len(Submission.objects.all().is_within(location).is_complete(group))
        missing = len(Submission.objects.all().is_within(location).is_missing(group))
        partial = len(Submission.objects.all().is_within(location).is_partial(group))

        group_summary = {'complete': complete, 'missing': missing, 'partial': partial}

        summary[group.name.lower()] = group_summary

    return summary
