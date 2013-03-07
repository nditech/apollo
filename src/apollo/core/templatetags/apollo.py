from django import template
from ..models import *

register = template.Library()


@register.filter
def keyvalue(value, key):
    try:
        return value[key]
    except KeyError:
        return ''


@register.filter
def sortedlist(value):
    return sorted(value)


@register.filter
def groupsel(value, pk):
    try:
        return value['group_%d' % pk]
    except KeyError:
        return None


@register.inclusion_tag('core/activity_info.html')
def activity_name(request=None):
    activity = request.session.get('activity', Activity.default())
    return {'activity': activity}


@register.inclusion_tag('core/analysis_menu.html')
def analysis_menu(request=None):
    activity = request.session.get('activity', Activity.default())
    if activity:
        forms = activity.forms.all().order_by('pk')
    else:
        forms = Form.objects.all().order_by('pk')
    return {'forms': forms}


@register.inclusion_tag('core/forms_menu.html')
def forms_menu(request=None):
    activity = request.session.get('activity', Activity.default())
    if activity:
        checklist_forms = activity.forms.filter(type='CHECKLIST').order_by('pk')
        incident_forms = activity.forms.filter(type='INCIDENT').order_by('pk')
    else:
        checklist_forms = Form.objects.filter(type='CHECKLIST').order_by('pk')
        incident_forms = Form.objects.filter(type='INCIDENT').order_by('pk')
    return {
        'checklist_forms': checklist_forms,
        'incident_forms': incident_forms
    }


@register.inclusion_tag('core/submission_filter.html')
def submission_filter(form, filter_form):
    form = form if isinstance(form, Form) else Form.objects.get(pk=form)
    form_groups = FormGroup.objects.filter(form=form)
    return {'form_groups': form_groups, 'form': form, 'filter_form': filter_form}


@register.inclusion_tag('core/submission_header.html')
def submission_header(form, permissions):
    form = form if isinstance(form, Form) else Form.objects.get(pk=form)
    location_types = LocationType.objects.filter(on_display=True)
    form_groups = FormGroup.objects.filter(form=form)
    form_fields = FormField.objects.filter(group__form=form).order_by('tag')
    return {'location_types': location_types, 'form_groups': form_groups,
            'form': form, 'form_fields': form_fields, 'perms': permissions}


@register.inclusion_tag('core/submission_items.html')
def submission_items(submissions, form, permissions):
    form = form if isinstance(form, Form) else Form.objects.get(pk=form)
    location_types = LocationType.objects.filter(on_display=True)
    form_groups = FormGroup.objects.filter(form=form)
    form_fields = FormField.objects.filter(group__form=form).order_by('tag')
    return {'submissions': submissions, 'location_types': location_types,
        'form_groups': form_groups, 'form': form, 'form_fields': form_fields,
        'perms': permissions}


@register.simple_tag
def get_location_for_type(submission, location_type):
    return submission.get_location_for_type(location_type) or ''


@register.filter
def is_complete(submission, group):
    return submission.is_complete(group)


@register.filter
def is_missing(submission, group):
    return submission.is_missing(group)


@register.filter
def is_partial(submission, group):
    return submission.is_partial(group)


@register.inclusion_tag('core/analysis_breadcrumb_navigation.html')
def analysis_breadcrumb_navigation(form, location=None, tag=None):
    form = form if isinstance(form, Form) else Form.objects.get(pk=form)
    try:
        location = location if isinstance(location, Location) else Location.objects.get(pk=location)
    except Location.DoesNotExist:
        location = Location.root()

    return {'locations': reversed(location.get_ancestors(include_self=True)), 'form': form, 'tag': tag}


@register.inclusion_tag('core/analysis_location_navigation.html')
def analysis_location_navigation(form, location=None, tag=None):
    form = form if isinstance(form, Form) else Form.objects.get(pk=form)
    try:
        location = location if isinstance(location, Location) else Location.objects.get(pk=location)
    except Location.DoesNotExist:
        location = Location.root()

    sub_locations = location.get_children()
    sub_locations.sort(key=lambda location: location.name)

    return {'locations': sub_locations, 'form': form, 'tag': tag}


@register.inclusion_tag('core/send_message_modal.html')
def send_message(recipients=0):
    return {'recipients': recipients}
