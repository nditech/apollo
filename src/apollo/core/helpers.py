from .models import FormField, Location, LocationType
from django.conf import settings


def memoize(f):
    """ Memoization decorator for functions taking one or more arguments. """
    class memodict(dict):
        def __init__(self, f):
            self.f = f

        def __call__(self, *args):
            return self[args]

        def __missing__(self, key):
            ret = self[key] = self.f(*key)
            return ret
    return memodict(f)


def generate_dashboard_summary(submission_queryset, group=None, locationtype=None):
    summary = []

    print locationtype

    if not locationtype:
        locationtype = filter(lambda lt: lt.on_dashboard == True, LocationType.root().get_descendants())[0]

    try:
        next_location_type = filter(lambda lt: lt.on_dashboard == True, locationtype.get_children())[0]
    except IndexError:
        next_location_type = locationtype

    # filter out and only select checklists to be filled by observers
    if group:
        try:
            for location in Location.objects.filter(type=next_location_type).order_by('name'):
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
    try:
        _obj = getattr(obj, attributes[0])
        if len(attributes) == 1:
            return _obj
        else:
            return r_getattr(_obj, '.'.join(attributes[1:]))
    except AttributeError:
        return ""


@memoize
def get_centroid_coords(pk):
    loc = Location.objects.get(pk=pk)
    if loc.poly:
        return (loc.poly.centroid.y, loc.poly.centroid.x)


# obtain the markers for incident
def get_incident_markers(form, submissions, location_type, tag=False):
    markers = []
    tags = FormField.objects.filter(group__form=form).values_list('tag', flat=True)

    for submission in submissions:
        locations = filter(lambda x: x['type'] == location_type, submission.location.nx_ancestors(include_self=True))
        if locations:
            incidents = filter(lambda x: x in tags, submission.data.keys()) if not tag else [0]
            for x in range(len(incidents)):
                marker = get_centroid_coords(locations[0]['id'])
                if marker:
                    markers.append(marker)
        elif submission.location.poly:
            incidents = filter(lambda x: x in tags, submission.data.keys()) if not tag else [0]
            for x in range(len(incidents)):
                marker = get_centroid_coords(submission.location.pk)
                if marker:
                    markers.append(marker)

    return markers
