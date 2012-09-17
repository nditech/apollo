import ast
from tastypie import fields
from tastypie.authorization import DjangoAuthorization, Authorization
from tastypie.resources import ModelResource
from .models import *


class LocationTypeResource(ModelResource):
    class Meta:
        queryset = LocationType.objects.all()
        resource_name = 'locationtype'
        excludes = ['level', 'lft', 'rght', 'tree_id', 'in_form']


class LocationResource(ModelResource):
    type = fields.ForeignKey(LocationTypeResource, 'type', full=True)
    parent = fields.ForeignKey('self', 'parent', full=True, null=True, blank=True)

    class Meta:
        queryset = Location.objects.all()
        resource_name = 'location'
        excludes = ['level', 'lft', 'rght', 'tree_id', 'in_form']


class PartnerResource(ModelResource):
    class Meta:
        queryset = Partner.objects.all()
        resource_name = 'partner'


class RoleResource(ModelResource):
    class Meta:
        queryset = ObserverRole.objects.all()
        resource_name = 'role'


class ContactResource(ModelResource):
    location = fields.ForeignKey(LocationResource, 'location', full=True)
    supervisor = fields.ForeignKey('self', 'supervisor', null=True, blank=True, full=True)
    role = fields.ForeignKey(RoleResource, 'role', full=True)
    partner = fields.ForeignKey(PartnerResource, 'partner', null=True, blank=True, full=True)

    class Meta:
        queryset = Observer.objects.all()
        resource_name = 'contact'
        authorization = DjangoAuthorization()

    def dehydrate_data(self, bundle):
        return ast.literal_eval(bundle.data['data'])


class FormResource(ModelResource):
    class Meta:
        queryset = Form.objects.all()
        resource_name = 'form'
        fields = ['name']


class FormGroupResource(ModelResource):
    form = fields.ForeignKey(FormResource, 'form', readonly=True, full=True)

    class Meta:
        queryset = Form.objects.all()
        resource_name = 'formgroup'


class SubmissionResource(ModelResource):
    contact = fields.ForeignKey(ContactResource, 'observer', full=True, readonly=True)
    form = fields.ForeignKey(FormResource, 'form', full=True)

    class Meta:
        queryset = Submission.objects.all()
        resource_name = 'submission'
        authorization = Authorization()
        excludes = ['created', 'updated']

    def dehydrate_data(self, bundle):
        return ast.literal_eval(bundle.data['data'])
