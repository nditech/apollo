from django import template
from ..models import *

register = template.Library()


@register.filter
def keyvalue(value, key):
    return value.get(key, '')


@register.filter
def groupsel(value, pk):
    try:
        return value['group_%d' % pk]
    except KeyError:
        return None


@register.inclusion_tag('core/forms_menu.html')
def forms_menu():
    forms = Form.objects.all()
    return {'forms': forms}


@register.inclusion_tag('core/submission_filter.html')
def submission_filter(form, filter_form):
    form = form if isinstance(form, Form) else Form.objects.get(pk=form)
    form_groups = FormGroup.objects.filter(form=form)
    return {'form_groups': form_groups, 'form': form, 'filter_form': filter_form}


@register.inclusion_tag('core/submission_header.html')
def submission_header(form):
    form = form if isinstance(form, Form) else Form.objects.get(pk=form)
    location_types = LocationType.objects.filter(on_display=True)
    form_groups = FormGroup.objects.filter(form=form)
    form_fields = FormField.objects.filter(group__form=form)
    return {'location_types': location_types, 'form_groups': form_groups,
        'form': form, 'form_fields': form_fields}


@register.inclusion_tag('core/submission_items.html')
def submission_items(submissions, form):
    form = form if isinstance(form, Form) else Form.objects.get(pk=form)
    location_types = LocationType.objects.filter(on_display=True)
    form_groups = FormGroup.objects.filter(form=form)
    form_fields = FormField.objects.filter(group__form=form)
    return {'submissions': submissions, 'location_types': location_types,
        'form_groups': form_groups, 'form': form, 'form_fields': form_fields}


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
