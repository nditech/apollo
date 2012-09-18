from django.conf.urls.defaults import *
from tastypie.api import Api
from .api import *

v2_api = Api(api_name='v2')

v2_api.register(ContactResource())
v2_api.register(LocationResource())
v2_api.register(LocationTypeResource())
v2_api.register(PartnerResource())
v2_api.register(RoleResource())
v2_api.register(FormResource())
v2_api.register(FormGroupResource())
v2_api.register(SubmissionResource())


urlpatterns = patterns('',
    url(r'^api/', include(v2_api.urls)),
)
