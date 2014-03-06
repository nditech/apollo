from __future__ import unicode_literals
from django.conf.urls import patterns, url
from core.views import (
    DashboardView, EventSelectionView
)


urlpatterns = patterns('',
    url(r'^$', DashboardView.as_view(), name='dashboard'),
    url(r'^event/$', EventSelectionView.as_view(), name='event_selection'),
)
