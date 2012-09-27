from django.conf.urls.defaults import *
from django.views.generic.base import TemplateView
from tastypie.api import Api
from .api import *

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


class TemplatePreview(TemplateView):
    def dispatch(self, request, *args, **kwargs):
        self.template_name = kwargs['template_name']
        return super(TemplateView, self).dispatch(request, *args, **kwargs)


urlpatterns = patterns('',
    url(r'^api/', include(v2_api.urls)),
    url(r'^tpl/(?P<template_name>.+)/?', TemplatePreview.as_view())
)

#authentication urls
urlpatterns += patterns('',
    (r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'core/login.html'}),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout_then_login')
)
