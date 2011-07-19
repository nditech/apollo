from django.conf.urls.defaults import *
from api import *
from tastypie.api import Api

api = Api()
api.register(ContactResource())
api.register(ContactRoleResource())
api.register(LocationResource())
api.register(LocationTypeResource())

urlpatterns = patterns('',
    url(r'^api/', include(api.urls)),
)

#authentication urls
urlpatterns += patterns('',
    (r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'psc/login.html'}),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout_then_login')
)
