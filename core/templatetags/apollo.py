from django import template
from ..models import *

register = template.Library()


@register.inclusion_tag('core/forms_menu.html')
def forms_menu():
    forms = Form.objects.all()
    return {'forms': forms}


@register.inclusion_tag('core/submission_header.html')
def submission_header(form):
    location_types = LocationType.objects.filter(on_display=True)
    form_groups = FormGroup.objects.filter(form=form) if isinstance(form, Form) else FormGroup.objects.filter(form__pk=form)
    return {'location_types': location_types, 'form_groups': form_groups}


@register.inclusion_tag('core/submission_items.html')
def submission_items(submissions):
    location_types = LocationType.objects.filter(on_display=True)
    form_groups = FormGroup.objects.filter(form=form) if isinstance(form, Form) else FormGroup.objects.filter(form__pk=form)

    return {'submissions': submissions, 'location_types': location_types, 'form_groups': form_groups}
