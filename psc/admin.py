#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.contrib import admin
from .models import LGA, RegistrationCenter, VRChecklist, VRIncident, DCOChecklist, DCOIncident, Observer

admin.site.register(LGA)
admin.site.register(RegistrationCenter)
admin.site.register(VRChecklist)
admin.site.register(VRIncident)
admin.site.register(DCOChecklist)
admin.site.register(DCOIncident)
admin.site.register(Observer)
