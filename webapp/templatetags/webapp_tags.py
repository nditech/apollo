from django import template
from django.conf import settings

register = template.Library()

@register.simple_tag
def app_templates(context):
    '''imports and extracts all javascript templates from installed applications 
    in preparation to send to the browser'''
    templates = ""
    for app in settings.INSTALLED_APPS:
        try:
            exec 'from %s import views as %s' % (app, app.split(".")[-1])
            exec "templates += %s.app_templates(context)" % app.split(".")[-1]
        except (ImportError, AttributeError, NameError):
            pass
    return templates