from tastypie.resources import ModelResource
from tastypie.authentication import Authentication
from tastypie.authorization import Authorization, DjangoAuthorization
from tastypie import fields
from webapp.models import *
from rapidsms.models import Contact

class LocationTypeResource(ModelResource):
    class Meta:
        queryset = LocationType.objects.all()
        resource_name = 'location_type'

class LocationResource(ModelResource):
    type = fields.ForeignKey(LocationTypeResource, 'type')
    
    class Meta:
        queryset = Location.objects.all()
        resource_name = 'location'

class ContactRoleResource(ModelResource):
    class Meta:
        queryset = ObserverRole.objects.all()
        resource_name = 'role'

class ContactResource(ModelResource):
    role = fields.ForeignKey(ContactRoleResource, 'role')
    location = fields.ForeignKey(LocationResource, 'location')
    supervisor = fields.ForeignKey('ContactResource', 'supervisor', null=True, blank=True)
    
    class Meta:
        queryset = Contact.objects.all()
        resource_name = 'contact'
        allowed_methods = ['get', 'put', 'post', 'delete']
        authentication = Authentication()
        authorization = Authorization()