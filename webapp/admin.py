#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.contrib import admin
from mptt.admin import MPTTModelAdmin

from models import *
from utility_models import *

admin.site.register(LocationType, MPTTModelAdmin)
admin.site.register(Location, MPTTModelAdmin)
admin.site.register(ObserverRole)
admin.site.register(Checklist)
admin.site.register(ChecklistForm)
admin.site.register(ChecklistQuestionType)
admin.site.register(ChecklistQuestion)
admin.site.register(ChecklistQuestionOption)
admin.site.register(ChecklistResponse)
admin.site.register(IncidentForm)
admin.site.register(IncidentResponse)
admin.site.register(Incident)
