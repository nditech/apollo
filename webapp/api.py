from django.conf.urls.defaults import *
from tastypie.resources import ModelResource
from tastypie.authentication import Authentication
from tastypie.authorization import Authorization, DjangoAuthorization
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.utils import trailing_slash
from tastypie import fields
from webapp.models import *
from rapidsms.models import Contact, Connection, Backend
from rapidsms.contrib.messagelog.models import Message

class LocationTypeResource(ModelResource):    
    class Meta:
        queryset = LocationType.objects.all()
        resource_name = 'location_type'
        filtering = {
            'name': ALL,
            'code': ALL,
            'parent': ALL_WITH_RELATIONS,
        }
        ordering = ['name', 'code']
        excludes = ['level', 'lft', 'rght', 'tree_id', 'in_form']


class LocationResource(ModelResource):
    type = fields.ForeignKey(LocationTypeResource, 'type', readonly=True, null=True, blank=True, full=True)
    parent = fields.ForeignKey('self', 'parent', readonly=True, null=True, blank=True, full=True)
    
    class Meta:
        queryset = Location.objects.select_related()
        resource_name = 'location'
        filtering = {
            'name': ALL,
            'code': ALL,
            'type': ALL_WITH_RELATIONS,
            'parent': ALL_WITH_RELATIONS,
            'id': ('exact',),
        }
        ordering = ['name', 'code', 'type__code']
        excludes = ['level', 'lft', 'rght', 'tree_id']
    
    def dehydrate(self, bundle):
            if bundle.obj.type.name == 'Ward':
                bundle.data['label'] = '%s - %s' % (bundle.obj.parent.name, bundle.obj.name)
            elif bundle.obj.type.name == 'Polling District':
                bundle.data['label'] = '%s - %s' % (bundle.obj.parent.parent.name, bundle.obj.name)
            elif bundle.obj.type.name == 'Polling Station':
                bundle.data['label'] = '%s - %s - %s' % (bundle.obj.parent.parent.parent.name, bundle.obj.parent.name, bundle.obj.name)
            elif bundle.obj.type.name == 'Polling Stream':
                bundle.data['label'] = '%s - %s - %s' % (bundle.obj.parent.parent.parent.parent.name, bundle.obj.parent.parent.name, bundle.obj.name)
            else:
                bundle.data['label'] = bundle.obj.name
            bundle.data['category'] = bundle.obj.type.name
            return bundle
    
    def override_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/search%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_search'), name='api_location_search'),
        ]
    
    def get_search(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)
        
        # do the query
        locations = Location.objects.filter(name__icontains=request.GET.get('term', ''))[:10]
        sorted_locations = sorted(locations, key=lambda location: location.type.name)
        objects = []
        for location in sorted_locations:
            bundle = self.build_bundle(obj=location, request=request)
            bundle = self.full_dehydrate(bundle)
            objects.append(bundle)
        
        object_list = objects
        
        self.log_throttled_access(request)
        return self.create_response(request, object_list) 


class ContactRoleResource(ModelResource):
    class Meta:
        queryset = ObserverRole.objects.all()
        resource_name = 'contact_role'


class BackendResource(ModelResource):
    class Meta:
        queryset = Backend.objects.all()
        resource_name = 'backend'


class ConnectionResource(ModelResource):
    backend = fields.ForeignKey(BackendResource, 'backend', full=True)
    contact = fields.ForeignKey('webapp.api.ContactResource', 'contact')

    class Meta:
        queryset = Connection.objects.select_related()
        resource_name = 'connection'
        allowed_methods = ['get', 'put', 'post']
        authentication = Authentication()
        authorization = Authorization()
        filtering = {
            'identity': ALL,
        }
        ordering = ['identity']


class ContactResource(ModelResource):
    role = fields.ForeignKey(ContactRoleResource, 'role', full=True)
    location = fields.ForeignKey(LocationResource, 'location', full=True)
    supervisor = fields.ForeignKey('self', 'supervisor', null=True, blank=True, full=True)
    cell_coverage = fields.IntegerField('cell_coverage', null=True, blank=True)
    connections = fields.ToManyField(ConnectionResource, 'connection_set', readonly=True, full=True)
    
    class Meta:
        queryset = Contact.objects.select_related()
        resource_name = 'contact'
        allowed_methods = ['get', 'put', 'post', 'delete']
        authentication = Authentication()
        authorization = Authorization()
        filtering = {
            'connections': ALL_WITH_RELATIONS,
            'name': ('contains', 'icontains',),
            'observer_id': ('exact',),
            'location': ALL_WITH_RELATIONS,
            'partner': ('exact',),
            'cell_coverage': ('exact',),
        }


class ContactsResource(ModelResource):
    role = fields.ForeignKey(ContactRoleResource, 'role', full=True)
    location = fields.ForeignKey(LocationResource, 'location', full=True)
    supervisor = fields.ForeignKey('self', 'supervisor', null=True, blank=True, full=True)
    cell_coverage = fields.IntegerField('cell_coverage', null=True, blank=True)
    connections = fields.ToManyField(ConnectionResource, 'connection_set', readonly=True, full=True)
    
    class Meta:
        queryset = Contact.objects.select_related()
        resource_name = 'contacts'
        allowed_methods = ['get']
        authentication = Authentication()
        authorization = Authorization()
        filtering = {
            'connections': ALL_WITH_RELATIONS,
            'name': ('contains', 'icontains',),
            'observer_id': ('exact',),
            'location': ALL_WITH_RELATIONS,
            'partner': ('exact',),
            'cell_coverage': ('exact',),
        }
        ordering = ['observer_id', 'name', 'role', 'location', 'connections', 'partner']
    
    def dehydrate(self, bundle):
        bundle.data['label'] = "%s (%s)" % (bundle.obj.name, bundle.obj.observer_id)
        bundle.data['category'] = "%ss" % bundle.obj.role.name
        return bundle
            
    def build_filters(self, filters=None):
        if not filters:
            filters = {}

        orm_filters = super(ContactsResource, self).build_filters(filters)
        if orm_filters.has_key('location__id__exact'):
            id = orm_filters.pop('location__id__exact')
            orm_filters['location__id__in'] = Location.objects.get(id=id).get_descendants(True).values_list('id', flat=True)

        return orm_filters

    def override_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/search%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_search'), name='api_contact_search'),
        ]

    def get_search(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)

        # do the query
        contacts = Contact.objects.filter(observer_id__startswith=request.GET.get('term', '')).order_by('observer_id')[:10]
        objects = []
        for contact in contacts:
            bundle = self.build_bundle(obj=contact, request=request)
            bundle = self.full_dehydrate(bundle)
            objects.append(bundle)

        object_list = objects

        self.log_throttled_access(request)
        return self.create_response(request, object_list)


class ChecklistFormResource(ModelResource):
    class Meta:
        queryset = ChecklistForm.objects.all()
        resource_name = 'checklist_form'   


class IncidentFormResource(ModelResource):
    class Meta:
        queryset = IncidentForm.objects.all()
        resource_name = 'incident_form'      


class MessageResource(ModelResource):
    contact = fields.ForeignKey('ContactResource', 'contact', full=True, readonly=True, null=True, blank=True)
    connection = fields.ForeignKey(ConnectionResource, 'connection', readonly=True, full=True)
    
    class Meta:
        queryset = Message.objects.select_related('contact', 'connection', 'connection__backend', 'connection__contact', 'contact__role', 'contact__location')
        resource_name = 'message'
        filtering = {
            'text': ('contains',),
            'direction': ('exact',),
            'connection': ALL_WITH_RELATIONS,
        }
        ordering = ['date', 'direction', 'connection', 'contact']