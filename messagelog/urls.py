from django.conf.urls.defaults import url, patterns

urlpatterns = patterns('',
    url(r'^export/(?P<format>\D{,4})/$', 'messagelog.views.export_message_log'),
)
