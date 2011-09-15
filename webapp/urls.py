from django.conf.urls.defaults import *
from django.conf import settings
from tastypie.resources import ModelResource, Resource
from tastypie.api import Api
from views import *
import inspect
# iteratively import all resources
for app in settings.INSTALLED_APPS:
    try:
        exec 'from %s.api import *' % app
    except ImportError:
        pass

api = Api()

# dynamically load all the resources
local_vars = locals()
resources = filter(lambda klass: inspect.isclass(local_vars[klass]) \
    and issubclass(local_vars[klass], Resource) and local_vars[klass] not in [ModelResource, Resource], local_vars.keys())

for resource in resources:
    api.register(local_vars[resource]())
    
urlpatterns = patterns('',
    url(r'^api/', include(api.urls)),
    url(r'^$', home),
    url(r'^sendsms/?', send_sms),
    url(r'^test/?', test)
)

#authentication urls
urlpatterns += patterns('',
    (r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'webapp/login.html'}),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout_then_login')
)
