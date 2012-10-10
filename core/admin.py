#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.contrib import admin
from mptt.admin import MPTTModelAdmin

from models import *

admin.site.register(LocationType, MPTTModelAdmin)
admin.site.register(Observer)
admin.site.register(ObserverRole)
admin.site.register(Partner)
admin.site.register(Form)
admin.site.register(FormGroup)
admin.site.register(FormField)
admin.site.register(FormFieldOption)
admin.site.register(Submission)
