from django.conf.urls import patterns, url

from .forms import FileuploadForm, MatchingForm
from .views import DataImportView


urlpatterns = patterns('',
    url(r'^$', DataImportView.as_view([FileuploadForm, MatchingForm]), name='tabimport'),
)
