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


class ChecklistFormResource(ModelResource):
    class Meta:
        queryset = ChecklistForm.objects.all()
        resource_name = 'form'   


class ChecklistQuestionTypeResource(ModelResource):
    class Meta:
        queryset = ChecklistQuestionType.objects.all()
        resource_name = 'type'


class ChecklistQuestionOptionResource(ModelResource):
    class Meta:
        queryset = ChecklistQuestionOption.objects.all()
        resource_name = 'option'


class ChecklistQuestionResource(ModelResource):
    form = fields.ForeignKey(ChecklistFormResource, 'form', readonly=True)
    type = fields.ForeignKey(ChecklistQuestionTypeResource, 'type', readonly=True)
    options = fields.ToManyField(ChecklistQuestionOptionResource, 'option', readonly=True)
    
    class Meta:
        queryset = ChecklistQuestion.objects.all()
        resource_name = 'question'


class ChecklistResponseResource(ModelResource):
    question = fields.ForeignKey(ChecklistQuestionResource, 'question', readonly=True)
    
    class Meta:
        queryset = ChecklistResponse.objects.all()
        resource_name = 'response'
        allowed_methods = ['get', 'put', 'post', 'delete']
        authentication = Authentication()
        authorization = Authorization()


class ChecklistResource(ModelResource):
    location = fields.ForeignKey(LocationResource, 'location')
    observer = fields.ForeignKey(ContactResource, 'observer')
    responses = fields.ToManyField(ChecklistResponseResource, 'response')
    
    class Meta:
        queryset = Checklist.objects.all()
        resource_name = 'checklist'
        allowed_methods = ['get', 'put', 'post', 'delete']
        authentication = Authentication()
        authorization = Authorization()
