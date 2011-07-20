from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        # helper URLs file that automatically serves the 'static' folder in
        # INSTALLED_APPS via the Django static media server (NOT for use in
        # production)
        (r'^', include('rapidsms.urls.static_media')),
    )

urlpatterns += patterns('',
    # PSC urls for default routing
    (r'^assets/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'assets'}), 
    (r'', include('webapp.urls')),
    (r'^comments/', include('django.contrib.comments.urls')),
) 
