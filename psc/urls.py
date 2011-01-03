from django.conf.urls.defaults import *
import views

urlpatterns = patterns('',
    (r'^/$', views.home),
    (r'^vr/?$', views.vr_list),
    (r'^vr/(?P<checklist_id>\d+)/?$', views.vr_checklist),
    (r'^vr/in/(?P<checklist_id>\d+)/?$', views.vr_incidents),
    (r'^vr/in/?$', views.vr_incidents_list),
    (r'^dco/?$', views.dco_list),
    (r'^dco/(?P<checklist_id>\d+)/?$', views.dco_checklist),
    (r'^dco/in/(?P<checklist_id>\d+)/?$', views.dco_incidents),
    (r'^msglog/$', views.message_log),
    (r'^actionlog/$', views.action_log),
)
