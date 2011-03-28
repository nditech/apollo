from django.conf.urls.defaults import *
import views

urlpatterns = patterns('',
    url(r'^$', views.home),
    url(r'^ajax_stats/?$', views.ajax_home_stats),
    url(r'^vr/?$', views.vr_checklist_list, name="vr_checklist_view"),
    url(r'^vr/export/?', views.vr_checklist_list, {'action': 'export'}, name="vr_checklist_export"),
    url(r'^vr/(?P<checklist_id>\d+)/?$', views.vr_checklist),
    url(r'^vr/in/?$', views.vr_incident_list, name="vr_incident_view"),
    url(r'^vr/in/export/?', views.vr_incident_list, {'action': 'export'}, name="vr_incident_export"),
    url(r'^vr/in/(?P<incident_id>\d+)/?$', views.vr_incident_update),
    url(r'^vr/in/add/?$', views.vr_incident_add),
    
    url(r'^dco/?$', views.dco_checklist_list, name="dco_checklist_view"),
    url(r'^dco/export/?', views.dco_checklist_list, {'action': 'export'}, name="dco_checklist_export"),
    url(r'^dco/(?P<checklist_id>\d+)/?$', views.dco_checklist),
    url(r'^dco/in/?$', views.dco_incident_list, name="dco_incident_view"),
    url(r'^dco/in/export/?', views.dco_incident_list, {'action': 'export'}, name="dco_incident_export"),
    url(r'^dco/in/(?P<incident_id>\d+)/?$', views.dco_incident_update),
    url(r'^dco/in/add/?$', views.dco_incident_add),
    
    url(r'^eday/?$', views.eday_checklist_list, name="eday_checklist_view"),
    url(r'^eday/export/?', views.eday_checklist_list, {'action': 'export'}, name="eday_checklist_export"),
    url(r'^eday/(?P<checklist_id>\d+)/?$', views.eday_checklist),
    url(r'^eday/in/?$', views.eday_incident_list, name="eday_incident_view"),
    url(r'^eday/in/export/?', views.eday_incident_list, {'action': 'export'}, name="eday_incident_export"),
    url(r'^eday/in/(?P<incident_id>\d+)/?$', views.eday_incident_update),
    url(r'^eday/in/add/?$', views.eday_incident_add),
    
    url(r'^msglog/$', views.message_log, name="msglog"),
    url(r'^msglog/export/?$', views.message_log, {'action': 'export'}, name="msglog_export"),
    
    url(r'^actionlog/$', views.action_log),
    
    url(r'^vr/zone/summary/?$', views.vr_zone_summary),
    url(r'^vr/state/summary/?$', views.vr_state_summary),
    
    url(r'^dco/zone/summary/?$', views.dco_zone_summary),
    url(r'^dco/state/summary/?$', views.dco_state_summary),
    
    url(r'^get-rcs-by-lga/(?P<lga_id>\d+)/?$', views.get_rcs_by_lga),
    url(r'^get-states-by-zone/(?P<zone>.+)/?$', views.get_states_by_zone),
    
    url(r'^vr/analysis/?$', views.vr_checklist_analysis),
    url(r'^eday/analysis/?$', views.eday_checklist_analysis),
    url(r'^vr/in/del/(?P<incident_id>\d+)/?$', views.vr_incident_delete),
    url(r'^dco/in/del/(?P<incident_id>\d+)/?$', views.dco_incident_delete),
    
    url(r'^eday/in/del/(?P<incident_id>\d+)/?$', views.eday_incident_delete),
    
    url(r'^sendmail/?$', views.send_mail),
    url(r'^contact/$', views.contact_list, name="contacts_list_view"),
    url(r'^contact/export/?$', views.contact_list, {'action': 'export'}, name="contacts_list_export"),
    url(r'^contactedit/(?P<contact_id>\d+)/$', views.contact_edit),
    url(r'^ajax_sendmsg$', views.ajax_send_message),
)

#authentication urls
urlpatterns += patterns('',
    (r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'psc/login.html'}),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout_then_login')
)
