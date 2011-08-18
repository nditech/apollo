from webapp.api import *
from webapp.models import *
from models import *
from django.db.models import Q

class ChecklistResponseResource(ModelResource):    
    class Meta:
        queryset = ZambiaChecklistResponse.objects.select_related()
        resource_name = 'checklist_response'
        allowed_methods = ['get', 'put', 'post', 'delete']
        authentication = Authentication()
        authorization = Authorization()


class ChecklistResource(ModelResource):
    location = fields.ForeignKey(LocationResource, 'location', full=True)
    observer = fields.ForeignKey(ContactResource, 'observer', full=True)
    response = fields.ToOneField(ChecklistResponseResource, 'response', full=True)

    class Meta:
        queryset = Checklist.objects.select_related()
        resource_name = 'checklist'
        allowed_methods = ['get', 'put', 'post', 'delete']
        authentication = Authentication()
        authorization = Authorization()
        filtering = {
            'date': ALL,
            'response': ALL_WITH_RELATIONS,
            'observer': ALL_WITH_RELATIONS,
            'location': ALL_WITH_RELATIONS,
        }
        ordering = ['location', 'date', 'observer']

    def build_filters(self, filters=None):
        if not filters:
            filters = {}

        orm_filters = super(ChecklistResource, self).build_filters(filters)
        
        if orm_filters.has_key('location__id__exact'):
            id = orm_filters.pop('location__id__exact')
            orm_filters['location__id__in'] = Location.objects.get(id=id).get_descendants(True).values_list('id', flat=True)
        
        if filters.get('setup_status'):
            status = filters.get('setup_status')
            if status == '1': # complete
                orm_filters.update(dict([('response__%s__isnull' % field, False) for field in \
                    ['A', 'B', 'CA', 'CB', 'CC', 'CD', 'CE', 'CF', 'CG', 'CH', 'D', 'E', 'EA', \
                    'EB', 'EC', 'F', 'G', 'H', 'J']]))
                
            elif status == '2': # missing
                orm_filters.update(dict([('response__%s__isnull' % field, True) for field in \
                    ['A', 'B', 'CA', 'CB', 'CC', 'CD', 'CE', 'CF', 'CG', 'CH', 'D', 'E', 'EA', \
                    'EB', 'EC', 'F', 'G', 'H', 'J']]))
                    
            elif status == '3': # partial
                query = None
                for field in ['A', 'B', 'CA', 'CB', 'CC', 'CD', 'CE', 'CF', 'CG', 'CH', 'D', \
                    'E', 'EA', 'EB', 'EC', 'F', 'G', 'H', 'J']:
                    if not query:
                        exec 'query = Q(response__%s__isnull=False)' % field
                    else:
                        exec 'query |= Q(response__%s__isnull=False)' % field
                orm_filters['pk__in'] = Checklist.objects.filter(query).values_list('id', flat=True)

        if filters.get('voting_status'):
            status = filters.get('voting_status')
            if status == '1': # complete
                orm_filters.update(dict([('response__%s__isnull' % field, False) for field in \
                    ['A', 'B', 'CA', 'CB', 'CC', 'CD', 'CE', 'CF', 'CG', 'CH', 'D', 'E', 'EA', \
                    'EB', 'EC', 'F', 'G', 'H', 'J']]))
                
            elif status == '2': # missing
                pass
            elif status == '3': # partial
                pass

        if filters.get('closing_status'):
            status = filters.get('closing_status')
            if status == '1': # complete
                pass
            elif status == '2': # missing
                pass
            elif status == '3': # partial
                pass

        if filters.get('counting_status'):
            status = filters.get('counting_status')
            if status == '1': # complete
                pass
            elif status == '2': # missing
                pass
            elif status == '3': # partial
                pass

        return orm_filters


class IncidentResponseResource(ModelResource):    
    class Meta:
        queryset = ZambiaIncidentResponse.objects.select_related()
        resource_name = 'incident_response'
        allowed_methods = ['get', 'put', 'post', 'delete']
        authentication = Authentication()
        authorization = Authorization()


class IncidentResource(ModelResource):
    location = fields.ForeignKey(LocationResource, 'location', full=True)
    observer = fields.ForeignKey(ContactResource, 'observer', full=True)
    response = fields.ToOneField(IncidentResponseResource, 'response', full=True)
    
    class Meta:
        queryset = Incident.objects.select_related()
        resource_name = 'incident'
        allowed_methods = ['get', 'put', 'post', 'delete']
        authentication = Authentication()
        authorization = Authorization()
        filtering = {
            'date': ALL,
            'observer': ALL_WITH_RELATIONS,
            'location': ALL_WITH_RELATIONS,
            'response': ALL_WITH_RELATIONS,
        }
        ordering = ['location', 'date', 'observer']
        