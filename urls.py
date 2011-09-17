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
        #url(r'^$', 'rapidsms.views.dashboard', name='rapidsms-dashboard'),
        #(r'^account/', include('rapidsms.urls.login_logout')),
        #(r'^httptester/', include('rapidsms.contrib.httptester.urls')),
        (r'^assets/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'assets'}), 
    )

urlpatterns += patterns('',
    # apolo urls for default routing
    (r'', include('webapp.urls')),
    (r'zambia/', include('zambia.urls')),
    (r'^', include('rapidsms.urls.static_media')),
    (r'^comments/', include('django.contrib.comments.urls')),
) 
