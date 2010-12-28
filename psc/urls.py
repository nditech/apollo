from django.conf.urls.defaults import *
import views

urlpatterns = patterns('',
    (r'^/?$', views.home),
    (r'^vr/?$', views.vr_list),
    (r'^vr/(?P<checklist_id>\d+)/?$', views.vr_checklist),
    (r'^vr/in/(?P<incident_id>\d+)/?$', views.vr_incident),
    (r'^dco/?$', views.dco_list),
    (r'^dco/(?P<checklist_id>\d+)/?$', views.dco_checklist),
    (r'^dco/in/(?P<incident_id>\d+)/?$', views.dco_incident),
    (r'^msglog/$', views.message_log),
)
