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
        resource_name = 'contact_role'


class ContactResource(ModelResource):
    role = fields.ForeignKey(ContactRoleResource, 'role', full=True)
    location = fields.ForeignKey(LocationResource, 'location', full=True)
    supervisor = fields.ForeignKey('ContactResource', 'supervisor', null=True, blank=True, full=True)
    
    class Meta:
        queryset = Contact.objects.all()
        resource_name = 'contact'
        allowed_methods = ['get', 'put', 'post', 'delete']
        authentication = Authentication()
        authorization = Authorization()


class ChecklistFormResource(ModelResource):
    class Meta:
        queryset = ChecklistForm.objects.all()
        resource_name = 'checklist_form'   


class ChecklistQuestionTypeResource(ModelResource):
    class Meta:
        queryset = ChecklistQuestionType.objects.all()
        resource_name = 'checklist_question_type'


class ChecklistQuestionOptionResource(ModelResource):
    class Meta:
        queryset = ChecklistQuestionOption.objects.all()
        resource_name = 'checklist_question_option'


class ChecklistQuestionResource(ModelResource):
    form = fields.ForeignKey(ChecklistFormResource, 'form', readonly=True)
    type = fields.ForeignKey(ChecklistQuestionTypeResource, 'type', readonly=True)
    options = fields.ToManyField(ChecklistQuestionOptionResource, 'options', readonly=True, full=True)
    
    class Meta:
        queryset = ChecklistQuestion.objects.all()
        resource_name = 'checklist_question'


class ChecklistResponseResource(ModelResource):
    question = fields.ForeignKey(ChecklistQuestionResource, 'question', readonly=True)
    
    class Meta:
        queryset = ChecklistResponse.objects.all()
        resource_name = 'checklist_response'
        allowed_methods = ['get', 'put', 'post', 'delete']
        authentication = Authentication()
        authorization = Authorization()


class ChecklistResource(ModelResource):
    location = fields.ForeignKey(LocationResource, 'location', full=True)
    observer = fields.ForeignKey(ContactResource, 'observer', full=True)
    responses = fields.ToManyField(ChecklistResponseResource, 'responses', full=True)
    
    class Meta:
        queryset = Checklist.objects.all()
        resource_name = 'checklist'
        allowed_methods = ['get', 'put', 'post', 'delete']
        authentication = Authentication()
        authorization = Authorization()


class IncidentFormResource(ModelResource):
    class Meta:
        queryset = IncidentForm.objects.all()
        resource_name = 'incident_form'

class IncidentResponseResource(ModelResource):
    form = fields.ForeignKey(IncidentFormResource, 'form', readonly=True)
    
    class Meta:
        queryset = IncidentResponse.objects.all()
        resource_name = 'incident_response'
        allowed_methods = ['get', 'put', 'post', 'delete']
        authentication = Authentication()
        authorization = Authorization()


class IncidentResource(ModelResource):
    location = fields.ForeignKey(LocationResource, 'location', full=True)
    observer = fields.ForeignKey(ContactResource, 'observer', full=True)
    responses = fields.ToManyField(IncidentResponseResource, 'responses', full=True)
    
    class Meta:
        queryset = Incident.objects.all()
        resource_name = 'incident'
        allowed_methods = ['get', 'put', 'post', 'delete']
        authentication = Authentication()
        authorization = Authorization()