#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.contrib import admin
from mptt.admin import MPTTModelAdmin

from models import *
from utility_models import *

admin.site.register(LocationType, MPTTModelAdmin)
admin.site.register(Location, MPTTModelAdmin)
admin.site.register(ObserverRole)
admin.site.register(ChecklistForm)
admin.site.register(Checklist)
admin.site.register(IncidentForm)
admin.site.register(Incident)
admin.site.register(Election)
admin.site.register(Party)
admin.site.register(PartyVote)
admin.site.register(ChecklistFormParty)