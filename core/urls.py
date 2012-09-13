from django.conf.urls.defaults import *
from .resources import *
from djangorestframework.views import ListOrCreateModelView, InstanceModelView, ListModelView
from djangorestframework.mixins import PaginatorMixin


class PaginatedListModelView(PaginatorMixin, ListModelView):
    limit = 2

urlpatterns = patterns('',
    url(r'^api/auth/', include('djangorestframework.urls', namespace='djangorestframework')),
    url(r'^api/locations/$', ListOrCreateModelView.as_view(resource=LocationResource)),
    url(r'^api/locations/(?P<pk>[^/]+)/?$', InstanceModelView.as_view(resource=LocationResource)),
    url(r'^api/locationtypes/$', PaginatedListModelView.as_view(resource=LocationTypeResource)),
    url(r'^api/locationtypes/(?P<pk>[^/]+)/?$', InstanceModelView.as_view(resource=LocationTypeResource), name='locationtype'),
)
