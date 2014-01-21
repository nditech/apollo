from django.conf.urls import patterns, url, include
from rapidsms.backends.kannel.views import KannelBackendView
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
v2_api.register(FormFieldResource())
v2_api.register(FormFieldOptionResource())
v2_api.register(SubmissionResource())


urlpatterns = patterns('',
    url(r'^$', DashboardView.as_view(), name='dashboard'),
    url(r'^dashboard/(?P<group>\d+)/(?P<locationtype>\d+)/?', DashboardView.as_view(), name='grouped_dashboard_with_locationtype'),
    url(r'^dashboard/(?P<group>\d+)/?', DashboardView.as_view(), name='grouped_dashboard'),
    
    url(r'^activity/$', ActivitySelectionView.as_view(), name="activity_selection"),

    url(r'^submissions/form/(?P<form>\d+)/?$', SubmissionListView.as_view(), name='submissions_list'),
    url(r'^submission/comments/add/?$', CommentCreateView.as_view(), name="add_comment"),
    url(r'^submission/(?P<pk>\d+)/?$', SubmissionEditView.as_view(), name='submission_edit'),
    url(r'^submission/(?P<pk>\d+)/version/(?P<version>\d+)/?$', SubmissionEditView.as_view(), name='submission_edit_with_version'),
    url(r'^submissions/form/(?P<form>\d+)/add/?$', SubmissionCreateView.as_view(), name='submission_add'),

    url(r'^incidents/form/(?P<form>\d+)/locationtype/(?P<locationtype>\d+)/incidents.csv$', IncidentsCSVView.as_view(), name='incidents_csv'),
    url(r'^incidents/form/(?P<form>\d+)/locationtype/(?P<locationtype>\d+)/location/(?P<location>\d+)/incidents.csv$', IncidentsCSVView.as_view(), name='incidents_csv_with_location'),
    

    url(r'^maps/zimbabwe/provinces\.html$', MapEmbedView.as_view(), name='map_embed'),

    url(r'^verifications/form/(?P<form>\d+)/?$', VerificationListView.as_view(), name='verifications_list'),
    url(r'^verification/(?P<pk>\d+)/?$', VerificationEditView.as_view(), name='verification_edit'),

    url(r'^submissions/analysis/process/form/(?P<form>\d+)/?$', SubmissionProcessAnalysisView.as_view(), name='submissions_analysis'),
    url(r'^submissions/analysis/process/form/(?P<form>\d+)/location/(?P<location_id>\d+)/?$', SubmissionProcessAnalysisView.as_view(), name='submissions_analysis_location'),
    url(r'^submissions/analysis/process/form/(?P<form>\d+)/tag/(?P<tag>[A-Z]+)/?$', SubmissionProcessAnalysisView.as_view(), name='submissions_analysis_tag'),
    url(r'^submissions/analysis/process/form/(?P<form>\d+)/location/(?P<location_id>\d+)/tag/(?P<tag>[A-Z]+)/?$', SubmissionProcessAnalysisView.as_view(), name='submissions_analysis_location_tag'),

    url(r'^submissions/analysis/results/form/(?P<form>\d+)/?$', SubmissionVotingResultsView.as_view(), name='results_analysis'),
    url(r'^submissions/analysis/results/form/(?P<form>\d+)/location/(?P<location_id>\d+)/?$', SubmissionVotingResultsView.as_view(), name='results_analysis_location'),

    url(r'^observers/?$', ContactListView.as_view(), name='contacts_list'),
    url(r'^observer/(?P<pk>\d+)/?$', ContactEditView.as_view(), name='contact_edit'),

    url(r'^locations/?$', LocationListView.as_view(), name='locations_list'),
    url(r'^locations/(?P<type_name>.+)\.(kml|kmz)$', LocationShapeListView.as_view(), name="locations_shapes"),
    url(r'^location/(?P<pk>\d+)/?$', LocationEditView.as_view(), name='location_edit'),

    url(r'^tpl/(?P<template_name>.+)/?$', TemplatePreview.as_view()),
)

# authentication urls
urlpatterns += patterns('',
    url(r'^accounts/login/$', 'apollo.core.views.login', {'template_name': 'core/login.html'}, name="user-login"),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout_then_login', name="user-logout")
)

urlpatterns += patterns('',
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^api/', include(v2_api.urls)),
    # messaging backends
    url(r'^backends/kannel/$', KannelBackendView.as_view(backend_name="kannel")),
)
