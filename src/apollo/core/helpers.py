from .models import Form, Activity, Location


def generate_dashboard_summary(submission_queryset, group=None):
    summary = []

    # filter out and only select checklists to be filled by observers
    if group:
        try:
            for location in Location.objects.filter(pk__in=[location['id'] for location in Location.root().nx_children()]).order_by('name'):
                complete = submission_queryset.filter(form__type="CHECKLIST").is_within(location).exclude(observer=None).is_complete(group).count()
                missing = submission_queryset.filter(form__type="CHECKLIST").is_within(location).exclude(observer=None).is_missing(group).count()
                partial = submission_queryset.filter(form__type="CHECKLIST").is_within(location).exclude(observer=None).is_partial(group).count()

                location_summary = {'name': location.name, 'id': location.pk, 'complete': complete, 'missing': missing, 'partial': partial}

                summary.append(location_summary)
        except (AttributeError, IndexError):
            # perhaps we didn't actually get a Form object
            pass
    else:
        try:
            form = submission_queryset.filter(form__type="CHECKLIST")[0].form
            for group in form.groups.all():
                complete = submission_queryset.filter(form__type="CHECKLIST").exclude(observer=None).is_complete(group).count()
                missing = submission_queryset.filter(form__type="CHECKLIST").exclude(observer=None).is_missing(group).count()
                partial = submission_queryset.filter(form__type="CHECKLIST").exclude(observer=None).is_partial(group).count()

                group_summary = {'name': group.name, 'id': group.pk, 'complete': complete, 'missing': missing, 'partial': partial}

                summary.append(group_summary)
        except (AttributeError, IndexError):
            # perhaps we didn't actually get a Form object
            pass

    return summary


# retrieve's attributes recursively
def r_getattr(obj, attr=''):
    attributes = attr.split('.')
    _obj = getattr(obj, attributes[0])
    if len(attributes) == 1:
        return _obj
    else:
        return r_getattr(_obj, '.'.join(attributes[1:]))
