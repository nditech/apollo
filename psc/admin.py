#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.contrib.auth.models import User
from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.models import Group
from django.contrib import admin
from .models import Zone, State, District, LGA, Ward, RegistrationCenter, VRChecklist, VRIncident, DCOChecklist, DCOIncident, Observer, EDAYChecklist, EDAYIncident
from .models import Partner, Party, Contesting

class ContestingAdmin(admin.ModelAdmin):
    list_display = ('state', 'party', 'code')
    
class ObserverAdmin(admin.ModelAdmin):
    list_display = ('observer_id', 'name')
    search_fields = ['observer_id',]
     
class GroupAdminWithCount(GroupAdmin):
    def user_count(self, obj):
        return obj.user_set.count()

    list_display = GroupAdmin.list_display + ('user_count',)

class RegistrationCenterAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'inec_code', 'parent')
    search_fields = ['name', 'inec_code',]
    
admin.site.unregister(Group)
admin.site.register(Group, GroupAdminWithCount)
admin.site.register(Zone)
admin.site.register(State)
admin.site.register(District)
admin.site.register(LGA)
admin.site.register(Ward)
admin.site.register(RegistrationCenter, RegistrationCenterAdmin)
admin.site.register(VRChecklist)
admin.site.register(VRIncident)
admin.site.register(DCOChecklist)
admin.site.register(DCOIncident)
admin.site.register(Observer, ObserverAdmin)
admin.site.register(Partner)
admin.site.register(EDAYChecklist)
admin.site.register(EDAYIncident)
admin.site.register(Party)
admin.site.register(Contesting, ContestingAdmin)