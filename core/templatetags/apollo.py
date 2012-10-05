from django import template
from ..models import *

register = template.Library()


@register.inclusion_tag('core/forms_menu.html')
def forms_menu():
    forms = Form.objects.all()
    return {'forms': forms}
