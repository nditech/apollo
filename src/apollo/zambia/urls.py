from django.conf.urls.defaults import *
from views import *

urlpatterns = patterns('',
    url(r'dashboard_stats/?', dashboard_stats),
    url(r'export_checklists/?', export_checklists),
    url(r'export_incidents/?', export_incidents),
    url(r'elections/process_analysis/?', process_analysis),
    url(r'elections/results_analysis/?', results_analysis),
    url(r'elections/station_status/?', station_status),
)