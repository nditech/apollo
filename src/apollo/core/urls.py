from django.conf.urls.defaults import *
from tastypie.api import Api
from .api import *
from .views import *

v2_api = Api(api_name='v2')

v2_api.register(ContactResource())
v2_api.register(MessageLogResource())
v2_api.register(LocationResource())
v2_api.register(LocationTypeResource())
v2_api.register(PartnerResource())
v2_api.register(RoleResource())
v2_api.register(FormResource())
v2_api.register(FormGroupResource())
v2_api.register(SubmissionResource())


urlpatterns = patterns('',
    url(r'^$', DashboardView.as_view(), name='dashboard'),
    url(r'^api/', include(v2_api.urls)),
    url(r'^submissions/form/(?P<form>\d+)/?$', SubmissionListView.as_view(), name='submissions_list'),
    url(r'^submissions/form/(?P<form>\d+)/export/?$', SubmissionListExportView.as_view(collection='observers'), name='submissions_list_export_observers'),
    url(r'^submissions/form/(?P<form>\d+)/export/master/?$', SubmissionListExportView.as_view(collection='master'), name='submissions_list_export_master'),
    url(r'^submission/(?P<pk>\d+)/?$', SubmissionEditView.as_view(), name='submission_edit'),
    url(r'^submissions/analysis/form/(?P<form>\d+)/?$', SubmissionAnalysisView.as_view(), name='submissions_analysis'),
    url(r'^submissions/analysis/form/(?P<form>\d+)/location/(?P<location_id>\d+)/?$', SubmissionAnalysisView.as_view(), name='submissions_analysis_location'),
    url(r'^submissions/analysis/form/(?P<form>\d+)/tag/(?P<tag>[A-Z]+)/?$', SubmissionAnalysisView.as_view(), name='submissions_analysis_tag'),
    url(r'^submissions/analysis/form/(?P<form>\d+)/location/(?P<location_id>\d+)/tag/(?P<tag>[A-Z]+)/?$', SubmissionAnalysisView.as_view(), name='submissions_analysis_location_tag'),
    url(r'^observers/?$', ContactListView.as_view(), name='contacts_list'),
    url(r'^observer/(?P<pk>\d+)/?$', ContactEditView.as_view(), name='contact_edit'),
    url(r'^locations/?$', LocationListView.as_view(), name='locations_list'),
    url(r'^location/(?P<pk>\d+)/?$', LocationEditView.as_view(), name='location_edit'),
    url(r'^tpl/(?P<template_name>.+)/?$', TemplatePreview.as_view()),
)

# authentication urls
urlpatterns += patterns('',
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'core/login.html'}, name="user-login"),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout_then_login', name="user-logout")
)
