from django.conf.urls.defaults import *
import views

urlpatterns = patterns('',
    (r'^$', views.home),
    (r'^vr/?$', views.vr_checklist_list),
    (r'^vr/(?P<checklist_id>\d+)/?$', views.vr_checklist),
    (r'^vr/in/?$', views.vr_incident_list),
    (r'^vr/in/(?P<incident_id>\d+)/?$', views.vr_incident_update),
    (r'^vr/in/add/?$', views.vr_incident_add),
    (r'^dco/?$', views.dco_checklist_list),
    (r'^dco/(?P<checklist_id>\d+)/?$', views.dco_checklist),
    (r'^dco/in/?$', views.dco_incident_list),
    (r'^dco/in/(?P<incident_id>\d+)/?$', views.dco_incident_update),
    (r'^dco/in/add/?$', views.dco_incident_add),
    (r'^msglog/$', views.message_log),
    (r'^actionlog/$', views.action_log),
    (r'^exportall/(?P<model>.+)/?$', views.export),
    (r'^vr/zone/summary/?$', views.vr_zone_summary),
    (r'^vr/state/summary/?$', views.vr_state_summary),
    (r'^dco/zone/summary/?$', views.dco_zone_summary),
    (r'^dco/state/summary/?$', views.dco_state_summary),
    (r'^get-rcs-by-lga/(?P<lga_id>\d+)/?$', views.get_rcs_by_lga),
    (r'^get-states-by-zone/(?P<zone>.+)/?$', views.get_states_by_zone),
    (r'^vr/analysis/?$', views.vr_checklist_analysis),
    (r'^vr/in/del/(?P<incident_id>\d+)/?$', views.vr_incident_delete),
    (r'^dco/in/del/(?P<incident_id>\d+)/?$', views.dco_incident_delete),
    (r'^sendmail/?$', views.send_mail),
    (r'^contact/$', views.contact_list),
    (r'^contactedit/(?P<contact_id>\d+)/$', views.contact_edit),
    (r'^ajax_sendmsg$', views.ajax_send_message),
)

#authentication urls
urlpatterns += patterns('',
    (r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'psc/login.html'}),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout_then_login')
)
