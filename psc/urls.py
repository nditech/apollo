from django.conf.urls.defaults import *
import views

urlpatterns = patterns('',
    (r'^/$', views.home),
    (r'^vr/?$', views.vr_checklist_list),
    (r'^vr/(?P<checklist_id>\d+)/?$', views.vr_checklist),
    (r'^vr/in/(?P<incident_id>\d+)/?$', views.vr_incident_update),
    (r'^vr/in/?$', views.vr_incident_list),
    (r'^vr/in/add?$', views.vr_incident_add),
    (r'^dco/?$', views.dco_list),
    (r'^dco/(?P<checklist_id>\d+)/?$', views.dco_checklist),
    (r'^dco/in/(?P<incident_id>\d+)/?$', views.dco_incident_update),
    (r'^dco/in/?$', views.dco_incident_list),
    (r'^dco/in/add?$', views.dco_incident_add),
    (r'^msglog/$', views.message_log),
    (r'^actionlog/$', views.action_log),
)
