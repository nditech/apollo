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

    def dehydrate_data(self, bundle):
        return ast.literal_eval(bundle.data['data'])


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
    groups = fields.ToManyField('core.api.FormGroupResource', 'groups', full=True)

    class Meta:
        queryset = Form.objects.all()
        resource_name = 'forms'
        always_return_data = True
        fields = ['name', 'type', 'trigger', 'field_pattern']
        authorization = Authorization()

    def dehydrate_options(self, bundle):
        return ast.literal_eval(bundle.data['options'])


class FormGroupResource(ModelResource):
    form = fields.ForeignKey(FormResource, 'form')
    fields = fields.ToManyField('core.api.FormFieldResource', 'fields', full=True)

    class Meta:
        queryset = FormGroup.objects.all()
        resource_name = 'formgroups'
        always_return_data = True
        excludes = ['_order']
        authorization = Authorization()


class FormFieldResource(ModelResource):
    group = fields.ForeignKey(FormGroupResource, 'group')
    options = fields.ToManyField('core.api.FormFieldOptionResource', 'options', full=True)

    class Meta:
        queryset = FormField.objects.all()
        resource_name = 'formfields'
        always_return_data = True
        excludes = ['allow_multiple', '_order']
        authorization = Authorization()


class FormFieldOptionResource(ModelResource):
    field = fields.ForeignKey(FormFieldResource, 'field')

    class Meta:
        queryset = FormFieldOption.objects.all()
        resource_name = 'formfieldoptions'
        always_return_data = True
        excludes = ['_order']
        authorization = Authorization()


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

    def dehydrate_overrides(self, bundle):
        return ast.literal_eval(bundle.data['overrides'])
