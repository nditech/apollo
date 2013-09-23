#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.contrib import admin
from models import *
from guardian.admin import GuardedModelAdmin
import reversion

class SubmissionAdmin(reversion.VersionAdmin):
	pass

admin.site.register(LocationType)
admin.site.register(Location)
admin.site.register(Observer)
admin.site.register(ObserverRole)
admin.site.register(Partner)
admin.site.register(Form, GuardedModelAdmin)
admin.site.register(FormGroup)
admin.site.register(FormField)
admin.site.register(FormFieldOption)
admin.site.register(Submission, SubmissionAdmin)
admin.site.register(ObserverDataField)
admin.site.register(Activity)
