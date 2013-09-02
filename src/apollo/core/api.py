import ast
from tastypie import fields
from tastypie.authentication import ApiKeyAuthentication
from tastypie.authorization import DjangoAuthorization, Authorization
from tastypie.constants import ALL
from tastypie.resources import ModelResource
from .models import *
from messagelog.models import MessageLog


class MessageLogResource(ModelResource):
    class Meta:
        queryset = MessageLog.objects.all()
        resource_name = 'messagelog'

        authentication = ApiKeyAuthentication()


class LocationTypeResource(ModelResource):
    class Meta:
        queryset = LocationType.objects.all()
        resource_name = 'locationtypes'
        excludes = ['on_display', 'in_form']

        authentication = ApiKeyAuthentication()


class LocationResource(ModelResource):
    type = fields.ForeignKey(LocationTypeResource, 'type', full=True)

    class Meta:
        queryset = Location.objects.all()
        resource_name = 'locations'
        excludes = ['in_form']
        filtering = {
            'name': ALL
        }


class PartnerResource(ModelResource):
    class Meta:
        queryset = Partner.objects.all()
        resource_name = 'partners'

        authentication = ApiKeyAuthentication()


class RoleResource(ModelResource):
    class Meta:
        queryset = ObserverRole.objects.all()
        resource_name = 'roles'

        authentication = ApiKeyAuthentication()


class ContactResource(ModelResource):
    location = fields.ForeignKey(LocationResource, 'location', full=True)
    supervisor = fields.ForeignKey('self', 'supervisor', null=True, blank=True, full=True)
    role = fields.ForeignKey(RoleResource, 'role', full=True)
    partner = fields.ForeignKey(PartnerResource, 'partner', null=True, blank=True, full=True)

    class Meta:
        queryset = Observer.objects.all()
        resource_name = 'contacts'
        filtering = {
            'observer_id': ALL
        }

    def dehydrate_data(self, bundle):
        return ast.literal_eval(bundle.data['data'])


class FormResource(ModelResource):
    class Meta:
        queryset = Form.objects.all()
        resource_name = 'forms'
        fields = ['name']

        authentication = ApiKeyAuthentication()


class FormGroupResource(ModelResource):
    form = fields.ForeignKey(FormResource, 'form', readonly=True, full=True)

    class Meta:
        queryset = FormGroup.objects.all()
        resource_name = 'formgroups'
        excludes = ['_order']

        authentication = ApiKeyAuthentication()


class SubmissionResource(ModelResource):
    contact = fields.ForeignKey(ContactResource, 'observer', full=True, readonly=True, null=True)
    location = fields.ForeignKey(LocationResource, 'location', full=True, readonly=True)
    form = fields.ForeignKey(FormResource, 'form', full=True)

    class Meta:
        queryset = Submission.objects.all()
        resource_name = 'submissions'

        authentication = ApiKeyAuthentication()

    def dehydrate_data(self, bundle):
        return ast.literal_eval(bundle.data['data'])
