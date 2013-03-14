from django.conf.urls.defaults import *
from django.contrib import admin
from django.views.generic.simple import redirect_to
from rapidsms.backends.kannel.views import KannelBackendView
from rapidsms_telerivet.views import TelerivetBackendView

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
    (r'^kannel/', KannelBackendView.as_view(backend_name='kannel')),
    (r'^telerivet/', TelerivetBackendView.as_view(backend_name='telerivet')),
    (r'^messages/', include('messagelog.urls')),
    (r'', include('core.urls')),
    (r'^favicon.ico', redirect_to, {'url': '/assets/ico/favicon.ico', 'permanent': True}),
)
