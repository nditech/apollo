from django.conf.urls.defaults import *
from views import *

urlpatterns = patterns('',
    url(r'dashboard_stats/?', dashboard_stats),
)