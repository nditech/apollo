#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.contrib import admin
from models import *
from reversion import admin as reversion

class ZambiaChecklistResponseAdmin(reversion.VersionAdmin):
    pass

class ZambiaIncidentResponseAdmin(reversion.VersionAdmin):
    pass

admin.site.register(ZambiaChecklistResponse, ZambiaChecklistResponseAdmin)
admin.site.register(ZambiaIncidentResponse, ZambiaIncidentResponseAdmin)