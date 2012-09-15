from django.conf.urls.defaults import *
from tastypie.api import Api
from .api import *

v1_api = Api(api_name='v1')

v1_api.register(ContactResource())
v1_api.register(LocationResource())
v1_api.register(LocationTypeResource())
v1_api.register(PartnerResource())
v1_api.register(RoleResource())
v1_api.register(FormResource())
v1_api.register(FormGroupResource())
v1_api.register(SubmissionResource())


urlpatterns = patterns('',
    url(r'^api/', include(v1_api.urls)),
)
