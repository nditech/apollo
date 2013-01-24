from django.conf.urls.defaults import *
from django.contrib import admin
from django.views.generic.simple import redirect_to
from rapidsms.backends.kannel.views import KannelBackendView

admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
)

urlpatterns += patterns('',
    # helper URLs file that automatically serves the 'static' folder in
    # INSTALLED_APPS via the Django static media server (NOT for use in
    # production)
    (r'^assets/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'assets'}),
)

urlpatterns += patterns('',
    # apollo urls for default routing
    (r'^kannel/', KannelBackendView.as_view(backend_name='kannel-smsc')),
    (r'^messages/', include('messagelog.urls')),
    (r'', include('core.urls')),
    (r'^favicon.ico', redirect_to, {'url': '/assets/images/favicon.ico', 'permanent': True}),
)
