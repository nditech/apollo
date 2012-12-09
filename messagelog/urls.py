from django.conf.urls.defaults import url, patterns
from .views import *

urlpatterns = patterns('',
    url(r'^$', MessageListView.as_view(), name='messages_list'),
    url(r'^export/(?P<format>\D{,4})/$', 'messagelog.views.export_message_log', name='messages_list_export'),
)
