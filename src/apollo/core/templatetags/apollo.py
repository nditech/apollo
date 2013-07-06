# -*- coding: utf-8 -*-
from django import template
from django.conf import settings
from core.models import *
from djorm_hstore.expressions import HstoreExpression as HE

register = template.Library()


@register.filter
def flag_status(value, flag_code):
    # returns a boolean if the value matches that of the
    # supplied flag_code
    try:
        return value == settings.FLAG_STATUSES.get(flag_code, None)[0]
    except IndexError:
        return None


@register.filter
def getvalue(value, attr):
    try:
        return getattr(value, attr)
    except AttributeError:
        return ''


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


@register.filter
def percent_of(numerator, denominator):
    try:
        return float(numerator if numerator else 0) / float(denominator if denominator else 0) * 100
    except ZeroDivisionError:
        return 0


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
    forms = filter(lambda form: request.user.has_perm('core.view_form', form), forms)
    return {'forms': forms}


@register.inclusion_tag('core/forms_menu.html')
def forms_menu(request=None, perms=None):
    activity = request.session.get('activity', Activity.default())
    if activity:
        checklist_forms = activity.forms.filter(type='CHECKLIST').order_by('pk')
        verification_forms = activity.forms.filter(type='CHECKLIST').where(HE('options').contains({'is_verifiable': '1'})).order_by('pk')
        incident_forms = activity.forms.filter(type='INCIDENT').order_by('pk')
    else:
        checklist_forms = Form.objects.filter(type='CHECKLIST').order_by('pk')
        verification_forms = Form.objects.filter(type='CHECKLIST').where(HE('options').contains({'is_verifiable': '1'})).order_by('pk')
        incident_forms = Form.objects.filter(type='INCIDENT').order_by('pk')

    # only add forms that the user has permission for
    checklist_forms = filter(lambda form: request.user.has_perm('core.view_form', form), checklist_forms)
    verification_forms = filter(lambda form: request.user.has_perm('core.view_form', form), verification_forms)
    incident_forms = filter(lambda form: request.user.has_perm('core.view_form', form), incident_forms)

    return {
        'checklist_forms': checklist_forms,
        'verification_forms': verification_forms,
        'incident_forms': incident_forms,
        'perms': perms
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
def get_location_for_type(submission, location_type, display_type=False):
    locations = filter(lambda loc: loc['type'] == location_type.name, submission.location.nx_ancestors(include_self=True))
    if display_type:
        return '{} · <em class="muted">{}</em>'.format(locations[0]['name'], locations[0]['type']) if locations else ''
    else:
        return locations[0]['name'] if locations else ''


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

    permitted_location_types = LocationType.objects.filter(on_analysis=True)

    return {'locations': reversed(filter(lambda loc: loc.type in permitted_location_types, location.get_ancestors(include_self=True))), 'form': form, 'tag': tag}


@register.inclusion_tag('core/analysis_location_navigation.html')
def analysis_location_navigation(form, location=None, tag=None):
    form = form if isinstance(form, Form) else Form.objects.get(pk=form)
    try:
        location = location if isinstance(location, Location) else Location.objects.get(pk=location)
    except Location.DoesNotExist:
        location = Location.root()

    permitted_location_types = LocationType.objects.filter(on_analysis=True)
    sub_locations = filter(lambda loc: loc.type in permitted_location_types, location.get_children())
    sub_locations.sort(key=lambda location: location.name)

    return {'locations': sub_locations, 'form': form, 'tag': tag}


@register.inclusion_tag('core/send_message_modal.html')
def send_message(recipients=0):
    return {'recipients': recipients}


@register.inclusion_tag('core/verification_filter.html')
def verification_filter(form, filter_form):
    form_flags = form.get_verification_flag_attributes('storage')
    return {'form_flags': form_flags, 'form': form, 'filter_form': filter_form}


@register.inclusion_tag('core/verification_header.html')
def verification_header(form, permissions):
    form = form if isinstance(form, Form) else Form.objects.get(pk=form)
    location_types = LocationType.objects.filter(on_display=True)
    form_flags = form.get_verification_flag_attributes('name')
    return {'location_types': location_types, 'form_flags': form_flags,
            'form': form, 'perms': permissions}


@register.inclusion_tag('core/verification_items.html')
def verification_items(submissions, form, permissions):
    form = form if isinstance(form, Form) else Form.objects.get(pk=form)
    location_types = LocationType.objects.filter(on_display=True)
    form_flags = form.get_verification_flag_attributes('storage')
    return {'submissions': submissions, 'location_types': location_types,
        'form_flags': form_flags, 'form': form, 'perms': permissions}
