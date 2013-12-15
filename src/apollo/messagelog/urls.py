from django.conf.urls.defaults import url, patterns
from .views import *

urlpatterns = patterns('',
    url(r'^$', MessageListView.as_view(), name='messages_list'),
)
